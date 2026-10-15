/*
 * XZIEL IQM2 optional viewmodel geometry bridge (stage 1).
 * Copyright 2026 XZIEL contributors, GPL-2.0-or-later, compatible with Vril.
 *
 * A valid .mdl is STILL authoritative for gameplay, hit detection, frames,
 * and animation timing. If xziel_iqm_viewmodels=1 and a .iqm sidecar exists,
 * this draws full-resolution bind-pose IQM mesh geometry in place of the MDL.
 *
 * This deliberately does NOT claim skeletal animation or PBR fidelity.
 * Invalid/unavailable IQM -> original MDL is drawn.
 */
#include "../../../nzportable_def.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#ifdef __ANDROID__
#include <android/log.h>
#define XIQM_ANDROID_LOG(...) __android_log_print(ANDROID_LOG_INFO,"XZIEL_IQM",__VA_ARGS__)
#else
#define XIQM_ANDROID_LOG(...) ((void)0)
#endif

#define XIQM_MAX_BYTES (32u * 1024u * 1024u)
#define XIQM_MAX_MESHES 256u
#define XIQM_MAX_VERTICES 250000u
#define XIQM_MAX_TRIANGLES 180000u

typedef struct {
    GLfloat p[3], uv[2], bind[3];
    unsigned char indices[4], weights[4];
} xiqm_vertex;
typedef struct {
    unsigned start, count;
    char material[96];
    int texture;
} xiqm_batch;
typedef struct {
    char model[MAX_QPATH];
    int available, first_draw_logged;
    unsigned triangles, num_batches;
    float fit_scale, fit_pos[3];
    /* Optional model-specific original-QuakeC ADS alignment. */
    float ads_amplitude_y, ads_delta_y, ads_delta_z;
    float ads_front[3], ads_optical_y, ads_optical_z;
    int ads_front_valid, ads_optical_ready, ads_optical_locked;
    int reload_first, reload_last, has_legacy_reload;
    xiqm_vertex *tri_vertices;
    xiqm_batch *batches;
    unsigned char *magazine_bits;
    unsigned magazine_faces;
    unsigned magazine_motion_logged;
    float magazine_drop, magazine_side;
} xiqm_state;

#define XIQM_SLOT_COUNT 24u
static xiqm_state xiqm_slots[XIQM_SLOT_COUNT];
static xiqm_state *xiqm_active = &xiqm_slots[0];
#define xiqm (*xiqm_active)
static cvar_t xziel_iqm_viewmodels = {"xziel_iqm_viewmodels", "0", true};
static cvar_t xziel_iqm_entities = {"xziel_iqm_entities", "0", true};
/* Original NZ:P hands-only MDL must be certified before enabling by default. */
static cvar_t xziel_iqm_original_hands = {"xziel_iqm_original_hands", "0", true};
static cvar_t xziel_iqm_preview_clip = {"xziel_iqm_preview_clip", "-1", true};

void Xziel_IQM_Init(void) {
    Cvar_RegisterVariable(&xziel_iqm_viewmodels);
    Cvar_RegisterVariable(&xziel_iqm_entities);
    Cvar_RegisterVariable(&xziel_iqm_original_hands);
    Cvar_RegisterVariable(&xziel_iqm_preview_clip);
}

/* IQM2 defines little-endian words. Supported Vril platforms here are LE. */
static uint32_t xiqm_u32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static float xiqm_f32(const unsigned char *p) {
    uint32_t bits = xiqm_u32(p);
    float f;
    memcpy(&f, &bits, sizeof(f));
    return f;
}
static int xiqm_span(size_t length, uint32_t start, uint32_t count, uint32_t stride) {
    return stride && start <= length && count <= (length - start) / stride;
}
static void xiqm_free(void) {
    free(xiqm.tri_vertices);
    free(xiqm.batches);
    free(xiqm.magazine_bits);
    xiqm.magazine_bits=NULL;
    xiqm.magazine_faces=0;
    xiqm.magazine_motion_logged=0;
    xiqm.magazine_drop=xiqm.magazine_side=0.0f;
    xiqm.tri_vertices = NULL;
    xiqm.batches = NULL;
    xiqm.triangles = 0;
    xiqm.num_batches = 0;
    xiqm.fit_scale = 1.0f;
    xiqm.fit_pos[0]=xiqm.fit_pos[1]=xiqm.fit_pos[2]=0.0f;
    xiqm.ads_amplitude_y=xiqm.ads_delta_y=xiqm.ads_delta_z=0.0f;
    xiqm.ads_front[0]=xiqm.ads_front[1]=xiqm.ads_front[2]=0.0f;
    xiqm.ads_optical_y=xiqm.ads_optical_z=0.0f;
    xiqm.ads_front_valid=xiqm.ads_optical_ready=xiqm.ads_optical_locked=0;
    xiqm.reload_first=xiqm.reload_last=xiqm.has_legacy_reload=0;
    xiqm.available = 0;
    xiqm.first_draw_logged = 0;
}
static const char *xiqm_name(const unsigned char *text, unsigned length, unsigned idx) {
    if (idx >= length || !memchr(text + idx, 0, length - idx))
        return NULL;
    return (const char *)(text + idx);
}
static void xiqm_strncpy(char *dst, size_t capacity, const char *src) {
    size_t n = strlen(src);
    if (n >= capacity)
        n = capacity - 1;
    memcpy(dst, src, n);
    dst[n] = 0;
}

#include "xiqm_animation.h"
/* Quake alias draw is implemented in gl_rmain.c; currententity is authoritative. */
extern void R_DrawAliasModel(entity_t *e);
static xzanim xza_slots[XIQM_SLOT_COUNT];
static xzanim *xza_active=&xza_slots[0];
#define xza (*xza_active)
/* Safe fragment: the source material can name a texture within a model folder
 * but must not navigate outside the game's virtual filesystem. */
static void xiqm_fragment(char *dst, size_t capacity, const char *src) {
    size_t j = 0;
    for (; *src && j + 1 < capacity; ++src) {
        unsigned char c = (unsigned char)*src;
        dst[j++] = (isalnum(c) || c == '_' || c == '-' || c == '.') ? c : '_';
    }
    dst[j] = 0;
}
/* Optional model-specific detachable magazine: a packed bitset generated
 * from real IQM triangle connectivity, NEVER a swap to the old MDL.
 * Other weapons without this sidecar retain their complete modern IQM mesh. */
static void xiqm_load_moving_magazine(const char *mdlpath) {
    char path[160];
    FILE *f=NULL;
    unsigned bytes,seen=0,i;
    unsigned char *raw;
    int n;
    size_t len=strlen(mdlpath);
    if (len<5 || len+12>=sizeof(path) || !xiqm.has_legacy_reload)
        return;
    snprintf(path,sizeof(path),"%.*s.iqmparts",(int)(len-4),mdlpath);
    n=COM_FOpenFile(path,&f);
    bytes=(xiqm.triangles+7u)/8u;
    if (!f || n != (int)(bytes+12u)) {
        if(f)fclose(f);
        XIQM_ANDROID_LOG("MOVING_MAGAZINE_NO_MASK model=%s file=%s",mdlpath,path);
        return;
    }
    raw=(unsigned char *)malloc((size_t)n);
    if (!raw) { fclose(f);return; }
    if (fread(raw,1,(size_t)n,f)!=(size_t)n ||
        memcmp(raw,"XIQMPART",8) || xiqm_u32(raw+8)!=xiqm.triangles) {
        free(raw);fclose(f);return;
    }
    fclose(f);
    for(i=0;i<xiqm.triangles;i++)
        if(raw[12+i/8u] & (1u << (i%8u)))seen++;
    if (seen==0 || seen>xiqm.triangles/5u) {
        free(raw);return;
    }
    xiqm.magazine_bits=(unsigned char *)malloc(bytes);
    if (!xiqm.magazine_bits){ free(raw);return; }
    memcpy(xiqm.magazine_bits,raw+12,bytes);
    xiqm.magazine_faces=seen;
    {
        float bottom=1.0e6f,top=-1.0e6f;
        for(i=0;i<xiqm.triangles;i++) {
            unsigned k;
            if (!(xiqm.magazine_bits[i/8u] & (1u << (i%8u)))) continue;
            for(k=0;k<3u;k++) {
                float z=xiqm.tri_vertices[i*3u+k].bind[2];
                if(z<bottom)bottom=z;
                if(z>top)top=z;
            }
        }
        if(top>bottom && top-bottom<10.0f) {
            /* Choreography scales automatically to the imported weapon. */
            xiqm.magazine_drop=(top-bottom)*1.08f;
            xiqm.magazine_side=(top-bottom)*0.32f;
        }
    }
    free(raw);
    XIQM_ANDROID_LOG("MODERN_MAGAZINE_COMPONENT model=%s faces=%u weapon_faces=%u down=%.3f side=%.3f",
                    mdlpath,seen,xiqm.triangles,xiqm.magazine_drop,xiqm.magazine_side);
}
static int xiqm_load(const char *mdlpath) {
    char path[128], folder[128];
    unsigned char *buf = NULL;
    float *xyz = NULL, *uv = NULL;
    FILE *f = NULL;
    int file_len;
    uint32_t text_count, ofs_text, mesh_count, ofs_meshes;
    uint32_t va_count, vertex_count, ofs_va, tri_count, ofs_tri;
    uint32_t position_offset = 0, uv_offset = 0, bone_offset = 0, weight_offset = 0;
    int has_indices = 0, has_weights = 0;
    unsigned i, j;
    int has_position = 0, has_uv = 0, ok = 0;
    size_t len, stem_len;
    xiqm.available = 0;
    xiqm.fit_scale = 1.0f;
    len = strlen(mdlpath);
    if (len < 5 || len + 1 >= sizeof(path) || strcmp(mdlpath + len - 4, ".mdl"))
        return 0;
    memcpy(path, mdlpath, len - 4);
    memcpy(path + len - 4, ".iqm", 5);
    file_len = COM_FOpenFile(path, &f);
    if (file_len < 124 || (unsigned)file_len > XIQM_MAX_BYTES || !f) {
        XIQM_ANDROID_LOG("SIDECAR_NOT_FOUND %s file_len=%d file=%p",path,file_len,(void*)f);
        if (f) fclose(f);
        return 0;
    }
    buf = (unsigned char *)malloc((size_t)file_len);
    if (!buf) goto done;
    if (fread(buf, 1, (size_t)file_len, f) != (size_t)file_len)
        goto done;
    if (memcmp(buf, "INTERQUAKEMODEL", 15) != 0 || buf[15] != 0 ||
        xiqm_u32(buf + 16) != 2 || xiqm_u32(buf + 20) != (uint32_t)file_len)
        goto done;
    text_count = xiqm_u32(buf + 28);
    ofs_text = xiqm_u32(buf + 32);
    mesh_count = xiqm_u32(buf + 36);
    ofs_meshes = xiqm_u32(buf + 40);
    va_count = xiqm_u32(buf + 44);
    vertex_count = xiqm_u32(buf + 48);
    ofs_va = xiqm_u32(buf + 52);
    tri_count = xiqm_u32(buf + 56);
    ofs_tri = xiqm_u32(buf + 60);
    if (mesh_count == 0 || mesh_count > XIQM_MAX_MESHES ||
        vertex_count == 0 || vertex_count > XIQM_MAX_VERTICES ||
        tri_count == 0 || tri_count > XIQM_MAX_TRIANGLES ||
        va_count > 32 || !xiqm_span(file_len, ofs_text, text_count, 1) ||
        !xiqm_span(file_len, ofs_meshes, mesh_count, 24) ||
        !xiqm_span(file_len, ofs_va, va_count, 20) ||
        !xiqm_span(file_len, ofs_tri, tri_count, 12))
        goto done;
    /* Require native little-endian 32-bit IEEE floats at POSITION and UV0.
     * Reject other accessor formats instead of reading wrong memory. */
    for (i = 0; i < va_count; i++) {
        const unsigned char *a = buf + ofs_va + 20u*i;
        uint32_t type = xiqm_u32(a), format = xiqm_u32(a+8);
        uint32_t components = xiqm_u32(a+12), offset = xiqm_u32(a+16);
        if (type == 0 && format == 7 && components == 3 &&
            xiqm_span(file_len, offset, vertex_count, 12)) {
            has_position = 1; position_offset = offset;
        } else if (type == 1 && format == 7 && components == 2 &&
                   xiqm_span(file_len, offset, vertex_count, 8)) {
            has_uv = 1; uv_offset = offset;
        } else if (type == 4 && format == 1 && components == 4 &&
                   xiqm_span(file_len, offset, vertex_count, 4)) {
            has_indices = 1; bone_offset = offset;
        } else if (type == 5 && format == 1 && components == 4 &&
                   xiqm_span(file_len, offset, vertex_count, 4)) {
            has_weights = 1; weight_offset = offset;
        }
    }
    if (!has_position) goto done;
    xiqm.tri_vertices = (xiqm_vertex *)calloc((size_t)tri_count * 3, sizeof(xiqm_vertex));
    xiqm.batches = (xiqm_batch *)calloc(mesh_count, sizeof(xiqm_batch));
    if (!xiqm.tri_vertices || !xiqm.batches) goto done;
    /* Important: expand indices to GL_TRIANGLES client arrays to support
     * Android GL without 32-bit element-index extensions. No decimation. */
    for (i = 0; i < tri_count; i++) {
        for (j = 0; j < 3; j++) {
            uint32_t index = xiqm_u32(buf + ofs_tri + 12u*i + 4u*j);
            xiqm_vertex *out = &xiqm.tri_vertices[3u*i+j];
            if (index >= vertex_count) goto done;
            out->p[0] = xiqm_f32(buf + position_offset + 12u*index);
            out->p[1] = xiqm_f32(buf + position_offset + 12u*index+4);
            out->p[2] = xiqm_f32(buf + position_offset + 12u*index+8);
            if (has_uv) {
                out->uv[0] = xiqm_f32(buf + uv_offset + 8u*index);
                out->uv[1] = xiqm_f32(buf + uv_offset + 8u*index+4);
            }
            memcpy(out->bind,out->p,sizeof(out->bind));
            if (has_indices && has_weights) {
                memcpy(out->indices,buf+bone_offset+4u*index,4);
                memcpy(out->weights,buf+weight_offset+4u*index,4);
            }
        }
    }
    stem_len = (size_t)(strrchr(path, '/') ? strrchr(path, '/') - path + 1 : 0);
    if (stem_len >= sizeof(folder)) goto done;
    memcpy(folder, path, stem_len);
    folder[stem_len] = 0;
    for (i = 0; i < mesh_count; i++) {
        const unsigned char *mesh = buf + ofs_meshes + 24u*i;
        uint32_t matid = xiqm_u32(mesh + 4);
        uint32_t first_vertex = xiqm_u32(mesh + 8);
        uint32_t num_vertex = xiqm_u32(mesh + 12);
        uint32_t first_tri = xiqm_u32(mesh + 16);
        uint32_t num_tri = xiqm_u32(mesh + 20);
        const char *mat = xiqm_name(buf + ofs_text, text_count, matid);
        xiqm_batch *b = &xiqm.batches[i];
        if (!mat || first_vertex > vertex_count || num_vertex > vertex_count - first_vertex ||
            first_tri > tri_count || num_tri > tri_count - first_tri) goto done;
        /* Cross-mesh vertex references must not be silently imported. */
        for (j = first_tri; j < first_tri + num_tri; j++) {
            uint32_t k;
            for (k=0; k<3; k++) {
                uint32_t index = xiqm_u32(buf + ofs_tri + 12u*j + 4u*k);
                if (index < first_vertex || index >= first_vertex + num_vertex)
                    goto done;
            }
        }
        b->start = first_tri * 3;
        b->count = num_tri * 3;
        b->texture = -1;
        xiqm_fragment(b->material, sizeof(b->material), mat);
    }
    if (!xza_load(&xza,buf,(size_t)file_len)) goto done;
    xza.weighted = has_indices && has_weights && xza.joints != 0;
    if (xza.weighted) {
        for (i=0; i<tri_count*3u; i++) {
            xiqm_vertex *v=&xiqm.tri_vertices[i];
            for (j=0; j<4; j++)
                if (v->weights[j] && v->indices[j]>=xza.joints) goto done;
        }
    }
    {
        char fitname[160], fitbuf[256];
        FILE *fitfile=NULL;
        int fitbytes;
        float s,tx,ty,tz,ads_y,delta_y,delta_z,reload_lo,reload_hi,fx,fy,fz;
        if (strlen(mdlpath)+5 < sizeof(fitname)) {
            snprintf(fitname,sizeof(fitname),"%.*s.iqmfit",(int)(strlen(mdlpath)-4),mdlpath);
            fitbytes=COM_FOpenFile(fitname,&fitfile);
            if (fitfile && fitbytes>0 && fitbytes<(int)sizeof(fitbuf) &&
                fread(fitbuf,1,(size_t)fitbytes,fitfile)==(size_t)fitbytes) {
                fitbuf[fitbytes]=0;
                int parsed=sscanf(fitbuf,"%f %f %f %f %f %f %f %f %f %f %f %f",
                                  &s,&tx,&ty,&tz,&ads_y,&delta_y,&delta_z,
                                  &reload_lo,&reload_hi,&fx,&fy,&fz);
                if (parsed>=4 && isfinite(s)&&isfinite(tx)&&isfinite(ty)&&isfinite(tz)&&
                    s>0.001f && s<1000.0f) {
                    xiqm.fit_scale=s;
                    xiqm.fit_pos[0]=tx;xiqm.fit_pos[1]=ty;xiqm.fit_pos[2]=tz;
                    if ((parsed==9 || parsed==12) && isfinite(ads_y) && isfinite(delta_y) &&
                        isfinite(delta_z) && isfinite(reload_lo) && isfinite(reload_hi) &&
                        ads_y>1.0f && ads_y<100.0f &&
                        delta_y>-100.0f && delta_y<100.0f &&
                        delta_z>-100.0f && delta_z<100.0f &&
                        reload_lo>=1.0f && reload_lo<=255.0f &&
                        reload_hi>reload_lo && reload_hi<=255.0f &&
                        reload_lo==(float)(int)reload_lo &&
                        reload_hi==(float)(int)reload_hi) {
                        xiqm.ads_amplitude_y=ads_y;
                        xiqm.ads_delta_y=delta_y;
                        xiqm.ads_delta_z=delta_z;
                        xiqm.reload_first=(int)reload_lo;
                        xiqm.reload_last=(int)reload_hi;
                        xiqm.has_legacy_reload=1;
                        if (parsed==12 && isfinite(fx) && isfinite(fy) && isfinite(fz) &&
                            fabsf(fx)<100.0f && fabsf(fy)<100.0f && fabsf(fz)<100.0f) {
                            xiqm.ads_front[0]=fx;
                            xiqm.ads_front[1]=fy;
                            xiqm.ads_front[2]=fz;
                            xiqm.ads_front_valid=1;
                        }
                        XIQM_ANDROID_LOG("ORIGINAL_QC_ADS y=%.3f delta_y=%.3f delta_z=%.3f reload_frames=%d..%d",
                                        ads_y,delta_y,delta_z,
                                        xiqm.reload_first,xiqm.reload_last);
                    }
                    Con_Printf("XZIEL IQM alignment %s scale=%.3f translate=%.3f %.3f %.3f\\n",fitname,s,tx,ty,tz);
                }
            }
            if (fitfile) fclose(fitfile);
        }
    }
    xiqm.triangles = tri_count;
    xiqm.num_batches = mesh_count;
    xiqm_load_moving_magazine(mdlpath);
    xiqm.available = 1;
    ok = 1;
    Con_Printf("XZIEL IQM: loaded %s meshes=%u triangles=%u vertices=%u\n",
               path, mesh_count, tri_count, vertex_count);
    XIQM_ANDROID_LOG("LOADED %s meshes=%u triangles=%u vertices=%u fit_scale=%.3f",
                     path, mesh_count, tri_count, vertex_count, xiqm.fit_scale);
done:
    if (f) fclose(f);
    free(buf);
    free(xyz);
    free(uv);
    if (!ok) {
        Con_Printf("XZIEL IQM: invalid %s, keeping original MDL\n", path);
        XIQM_ANDROID_LOG("REJECTED %s, using original MDL",path);
        xiqm_free();
        xza_clear(&xza);
    }
    return ok;
}
/* Frame-accurate trigger comes from the original server-authoritative
 * MDL frame range; the new procedural choreography is an EXPERIMENTAL visual
 * stand-in until the same high-poly weapon receives genuine rigged clips.
 * No old mesh is used, no animation timing/gameplay state is changed. */
static float xiqm_reload_progress(int frame) {
    if (!xiqm.has_legacy_reload || frame<xiqm.reload_first ||
        frame>xiqm.reload_last) return -1.0f;
    return (float)(frame-xiqm.reload_first)/
           (float)(xiqm.reload_last-xiqm.reload_first);
}
static float xiqm_smooth(float x) {
    if(x<0.0f)x=0.0f;
    if(x>1.0f)x=1.0f;
    return x*x*(3.0f-2.0f*x);
}
static float xiqm_magazine_motion(float progress) {
    if (progress<0.0f || !xiqm.magazine_bits) return 0.0f;
    /* Magazine release -> extract -> hold -> seat. This does not pretend
     * to be frame-for-frame BO3 animation. All frames are from original QC. */
    if (progress<0.28f) return xiqm_smooth(progress/0.28f);
    if (progress<0.62f) return 1.0f;
    if (progress<0.91f) return 1.0f-xiqm_smooth((progress-0.62f)/0.29f);
    return 0.0f;
}
static void xiqm_update_pose(float reload_progress) {
    unsigned i,k;
    int active=0;
    float magazine_movement=xiqm_magazine_motion(reload_progress);
    float magazine_side=0.0f;
    unsigned translated_vertices=0;
    if (reload_progress>=0.16f && reload_progress<=0.88f) {
        if(reload_progress<0.42f)
            magazine_side=xiqm_smooth((reload_progress-0.16f)/0.26f);
        else if(reload_progress<=0.66f)
            magazine_side=1.0f;
        else
            magazine_side=1.0f-xiqm_smooth((reload_progress-0.66f)/0.22f);
    }
    if (xziel_iqm_preview_clip.value>=0 && xza.weighted &&
        xziel_iqm_preview_clip.value<(float)xza.clips)
        active=xza_eval(&xza,(unsigned)xziel_iqm_preview_clip.value,(float)cl.time);
    for (i=0;i<xiqm.triangles*3u;i++) {
        xiqm_vertex *v=&xiqm.tri_vertices[i];
        unsigned sum=0;
        float accum[3]={0,0,0};
        if (active) {
            for(k=0;k<4;k++)sum+=v->weights[k];
            if(sum) {
                for(k=0;k<4;k++) {
                    float moved[3],factor;
                    if(!v->weights[k])continue;
                    xzm_point(&xza.skin[v->indices[k]],v->bind,moved);
                    factor=(float)v->weights[k]/(float)sum;
                    accum[0]+=moved[0]*factor;
                    accum[1]+=moved[1]*factor;
                    accum[2]+=moved[2]*factor;
                }
                memcpy(v->p,accum,sizeof(accum));
            } else memcpy(v->p,v->bind,sizeof(v->bind));
        } else memcpy(v->p,v->bind,sizeof(v->bind));
        if (magazine_movement>0.0f && xiqm.magazine_bits &&
            (xiqm.magazine_bits[(i/3u)/8u] & (1u << ((i/3u)%8u)))) {
            /* Real magazine triangles from THIS 14,450-face high-poly IQM.
             * Keep geometry, base-color UVs, material and normals intact. */
            /* Same modern magazine descends from receiver, drifts LEFT
             * on extraction, then inserts before source reload completes.
             * This deliberately does NOT resurrect the Quake MDL gun. */
            {
                float old_z=v->p[2];
                v->p[1]-=xiqm.magazine_side*magazine_side;
                v->p[2]-=xiqm.magazine_drop*magazine_movement;
                if (!xiqm.magazine_motion_logged && magazine_movement>=0.8f &&
                    fabsf(v->p[2]-old_z)>0.001f)
                    translated_vertices++;
            }
        }
    }
    /* The existing reload-start log only proves that the legacy frame range
     * was entered. This later probe proves the renderer actually translated
     * every selected high-poly IQM vertex in a nonzero extraction pose. */
    if (!xiqm.magazine_motion_logged && magazine_movement>=0.8f &&
        translated_vertices==xiqm.magazine_faces*3u &&
        xiqm.magazine_faces>0u) {
        XIQM_ANDROID_LOG("MAGAZINE_REAL_VERTEX_TRANSLATION model=%s faces=%u vertices=%u down=%.5f side=%.5f progress=%.3f",
                         xiqm.model,xiqm.magazine_faces,translated_vertices,
                         xiqm.magazine_drop*magazine_movement,
                         xiqm.magazine_side*magazine_side,reload_progress);
        xiqm.magazine_motion_logged=1;
    }
}
/* Fixed-function optical calibration: align the real front iron sight to
 * the projection's optical center. This is a MODEL transform, not an
 * aim-assist/gameplay change. No target locations or bullet trajectories are
 * touched. The source sight landmark comes from the actual GLB geometry. */
static float xiqm_cliprow(const GLfloat p[16],const GLfloat v[4],unsigned row) {
    return p[row]*v[0]+p[row+4]*v[1]+p[row+8]*v[2]+p[row+12]*v[3];
}
static void xiqm_aim_optical_sight(float fraction) {
    GLfloat m[16],p[16],pt[4],sy[4],sz[4];
    float px,py,ax,ay,bx,by,det,dy,dz;
    static int optical_attempt_logged=0, optical_fail_logged=0;
    unsigned k;
    if (!xiqm.ads_front_valid || fraction<=0.35f) {
        if (fraction<0.05f)xiqm.ads_optical_locked=0;
        return;
    }
    if (!xiqm.ads_optical_locked) {
        glGetFloatv(GL_MODELVIEW_MATRIX,m);
        glGetFloatv(GL_PROJECTION_MATRIX,p);
        for (k=0;k<4;k++) {
            pt[k]=m[k]*xiqm.ads_front[0]+m[k+4]*xiqm.ads_front[1]+
                  m[k+8]*xiqm.ads_front[2]+m[k+12];
            sy[k]=m[k+4]/xiqm.fit_scale;
            sz[k]=m[k+8]/xiqm.fit_scale;
        }
        px=xiqm_cliprow(p,pt,0);
        py=xiqm_cliprow(p,pt,1);
        ax=xiqm_cliprow(p,sy,0);ay=xiqm_cliprow(p,sy,1);
        bx=xiqm_cliprow(p,sz,0);by=xiqm_cliprow(p,sz,1);
        det=ax*by-ay*bx;
        if (!optical_attempt_logged) {
            XIQM_ANDROID_LOG("OPTICAL_CALC fraction=%.3f sight=(%.3f %.3f %.3f) clip=(%.3f %.3f) jacobian=(%.3f %.3f %.3f %.3f) det=%.8f fit=%.3f",
                fraction,xiqm.ads_front[0],xiqm.ads_front[1],xiqm.ads_front[2],
                px,py,ax,ay,bx,by,det,xiqm.fit_scale);
            optical_attempt_logged=1;
        }
        if (isfinite(det) && fabsf(det)>1.e-6f) {
            dy=(-px*by+bx*py)/det;
            dz=(-ax*py+ay*px)/det;
            if (!optical_fail_logged) {
                XIQM_ANDROID_LOG("OPTICAL_CORRECTION_CANDIDATE fraction=%.3f dy=%.3f dz=%.3f",fraction,dy,dz);
                optical_fail_logged=1;
            }
            if (isfinite(dy) && isfinite(dz) &&
                fabsf(dy)<24.0f && fabsf(dz)<24.0f) {
                xiqm.ads_optical_y=dy;
                xiqm.ads_optical_z=dz;
                xiqm.ads_optical_ready=1;
                if(fraction>=0.98f) {
                    xiqm.ads_optical_locked=1;
                    XIQM_ANDROID_LOG("OPTICAL_SIGHT_CENTERED model=%s adjust_y=%.3f adjust_z=%.3f",
                                     xiqm.model,dy,dz);
                }
            }
        }
    }
    if (xiqm.ads_optical_ready) {
        float blend=fraction*fraction; /* ease in with authoritative CSQC ADS */
        glTranslatef(0.0f,blend*xiqm.ads_optical_y/xiqm.fit_scale,
                    blend*xiqm.ads_optical_z/xiqm.fit_scale);
    }
}
static qboolean xiqm_draw_entity(entity_t *e, unsigned i) {
    GLboolean depth_was_enabled, blend_was_enabled, cull_was_enabled, texture_was_enabled;
    unsigned textured_batches=0;
    float ads_fraction=0.0f, ads_shift_y=0.0f, ads_shift_z=0.0f;
    float reload_progress=-1.0f;
    if (!e || !e->model || i>=XIQM_SLOT_COUNT)
        return false;
    xiqm_active=&xiqm_slots[i];
    xza_active=&xza_slots[i];
    if (strcmp(xiqm.model, e->model->name)) {
        xza_clear(&xza);
        xiqm_free();
        xiqm_strncpy(xiqm.model, sizeof(xiqm.model), e->model->name);
        xiqm_load(xiqm.model);
    }
    if (!xiqm.available)
        return false;
    /* No visual switch to MDL: the same IQM always draws while equipped.
     * Legacy weapon frame values are used only to time the new mesh pose. */
    {
        static int logged=0;
        float progress=(i<2)?xiqm_reload_progress(e->frame):-1.0f;
        if (progress>=0.0f && !logged) {
            XIQM_ANDROID_LOG("RELOAD_SAME_HIGH_POLY_IQM model=%s frame=%d movable_magazine_faces=%u",
                            xiqm.model,e->frame,xiqm.magazine_faces);
            logged=1;
        }
        xiqm_update_pose(progress);
    }

    depth_was_enabled=glIsEnabled(GL_DEPTH_TEST);
    blend_was_enabled=glIsEnabled(GL_BLEND);
    cull_was_enabled=glIsEnabled(GL_CULL_FACE);
    texture_was_enabled=glIsEnabled(GL_TEXTURE_2D);
    if (i<2)reload_progress=xiqm_reload_progress(e->frame);
    /* e->origin[1] is interpolated live by authoritative CSQC
     * ViewModel_GetADSPosition; no parallel ADS clock is introduced. */
    if (i<2 && xiqm.ads_amplitude_y>1.0f) {
        static int origin_samples=0;
        ads_fraction=e->origin[1]/xiqm.ads_amplitude_y;
        if (origin_samples<4 && fabsf(e->origin[1])>1.0f) {
            XIQM_ANDROID_LOG("ADS_ORIGIN_SAMPLE model=%s frame=%d origin=(%.3f %.3f %.3f) fraction=%.3f front_valid=%d",
                            xiqm.model,e->frame,e->origin[0],e->origin[1],e->origin[2],
                            ads_fraction,xiqm.ads_front_valid);
            origin_samples++;
        }
        if (ads_fraction<0.03f)ads_fraction=0.0f; /* avoid idle lateral bob */
        if (ads_fraction>1.0f)ads_fraction=1.0f;
        if (ads_fraction<0.0f)ads_fraction=0.0f;
        ads_shift_y=ads_fraction*xiqm.ads_delta_y;
        ads_shift_z=ads_fraction*xiqm.ads_delta_z;
    }
    glPushMatrix();
    R_RotateForEntity(e, e->scale);
    if (reload_progress>=0.0f)
        glRotatef(11.0f*sinf(reload_progress*3.14159265f),1.0f,0.0f,0.0f);
    glTranslatef(xiqm.fit_pos[0],xiqm.fit_pos[1]+ads_shift_y,xiqm.fit_pos[2]+ads_shift_z);
    glScalef(xiqm.fit_scale,xiqm.fit_scale,xiqm.fit_scale);
    if(i<2 && xiqm.ads_amplitude_y>1.0f)
        xiqm_aim_optical_sight(ads_fraction);
    glEnable(GL_DEPTH_TEST);
    glDisable(GL_BLEND);
    /* Diagnostic path keeps both sides visible until winding is verified. */
    glDisable(GL_CULL_FACE);
    glColor4f(1,1,1,1);
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glVertexPointer(3, GL_FLOAT, sizeof(xiqm_vertex), &xiqm.tri_vertices[0].p[0]);
    glTexCoordPointer(2, GL_FLOAT, sizeof(xiqm_vertex), &xiqm.tri_vertices[0].uv[0]);
    for (i = 0; i < xiqm.num_batches; ++i) {
        xiqm_batch *b = &xiqm.batches[i];
        if (b->texture == -1) {
            char prefix[128], texname[256];
            const char *slash = strrchr(xiqm.model, '/');
            size_t folder_len = slash ? (size_t)(slash - xiqm.model + 1) : 0;
            if (folder_len + strlen(b->material) + 1 < sizeof(texname)) {
                memcpy(prefix, xiqm.model, folder_len);
                prefix[folder_len] = 0;
                snprintf(texname, sizeof(texname), "%s%s", prefix, b->material);
                b->texture = Image_LoadImage(texname, IMAGE_PNG | IMAGE_TGA | IMAGE_JPG, 0, true, true);
                XIQM_ANDROID_LOG("TEXTURE model=%s material=%s path=%s id=%d",xiqm.model,b->material,texname,b->texture);
            }
            if (b->texture < 0) b->texture = -2; /* retry never until model changes */
        }
        if (b->texture >= 0) {
            glEnable(GL_TEXTURE_2D);
            Hyena_BindTexture(b->texture);
            textured_batches++;
        } else {
            glDisable(GL_TEXTURE_2D);
        }
        glDrawArrays(GL_TRIANGLES, (GLint)b->start, (GLsizei)b->count);
    }
    if (!xiqm.first_draw_logged) {
        XIQM_ANDROID_LOG("DRAWN model=%s triangles=%u textured_batches=%u ADS_source_y=%.3f correction_y=%.3f correction_z=%.3f",
                         xiqm.model,xiqm.triangles,textured_batches,
                         xiqm.ads_amplitude_y,xiqm.ads_delta_y,xiqm.ads_delta_z);
        xiqm.first_draw_logged=1;
    }
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    glDisableClientState(GL_VERTEX_ARRAY);
    glEnable(GL_TEXTURE_2D);
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);
    glColor4f(1,1,1,1);
    glPopMatrix();
    if (cull_was_enabled) glEnable(GL_CULL_FACE); else glDisable(GL_CULL_FACE);
    if (blend_was_enabled) glEnable(GL_BLEND); else glDisable(GL_BLEND);
    if (depth_was_enabled) glEnable(GL_DEPTH_TEST); else glDisable(GL_DEPTH_TEST);
    if (texture_was_enabled) glEnable(GL_TEXTURE_2D); else glDisable(GL_TEXTURE_2D);
    return true;
}

/* A verified stock-only hands MDL can overlay the modern IQM gun.
 * Its EXACT 46 original pose bytes are preserved, so authoritative e->frame
 * advances the hand reload without replacing the visible 14,450-face gun.
 * Use a deliberately separate model: NEVER render the old full MP40.
 * This is opt-in until geometry-ownership and Android camera QA pass.
 *
 * R_DrawAliasModel's upstream implementation uses global currententity in
 * several places, not only its argument. Only render with the real cl.viewent
 * as currententity, and restore its model pointer immediately afterwards.
 */
void Xziel_IQM_DrawOriginalHands(entity_t *e) {
    static model_t *hands=NULL;
    static int first_report=0;
    model_t *weapon;
    if (xziel_iqm_original_hands.value==0 || !e || !e->model ||
        e!=&cl.viewent || currententity!=e ||
        strcmp(e->model->name,"models/weapons/mp40/v_mp40.mdl")!=0)
        return;
    if (!hands) {
        hands=Mod_ForName("models/weapons/mp40/v_mp40_hands_only.mdl",false);
        if(!hands || hands->type!=mod_alias) {
            if(!first_report) {
                XIQM_ANDROID_LOG("ORIGINAL_HANDS_NOT_LOADED no safe 46-frame hands model");
                first_report=1;
            }
            hands=NULL;
            return;
        }
    }
    if(e->frame<0 || e->frame>=46) {
        XIQM_ANDROID_LOG("ORIGINAL_HANDS_FRAME_REJECT frame=%d",e->frame);
        return;
    }
    weapon=e->model;
    e->model=hands;
    R_DrawAliasModel(e);
    e->model=weapon;
    if(!first_report) {
        XIQM_ANDROID_LOG("ORIGINAL_HANDS_SAME_46_POSE model=%s frame=%d alongside=14450-face-IQM",hands->name,e->frame);
        first_report=1;
    }
}

/* Generic world alias integration: same IQM parser/skinner, no QuakeC change.
 * Slot caching is per unique model path; cvars default OFF to protect release.
 * Missing IQM falls straight back to the original MDL in R_DrawEntitiesOnList. */
qboolean Xziel_IQM_DrawViewModel(entity_t *e) {
    static int debug_first=0;
    if (!debug_first) {
        XIQM_ANDROID_LOG("VIEWMODEL_ENTRY enabled=%.1f model=%s",
                         xziel_iqm_viewmodels.value,
                         (e && e->model)?e->model->name:"(missing)");
        debug_first=1;
    }
    if (xziel_iqm_viewmodels.value==0 || !e || !e->model)
        return false;
    return xiqm_draw_entity(e, e==&cl.viewent2 ? 1u : 0u);
}
qboolean Xziel_IQM_DrawWorldEntity(entity_t *e) {
    static unsigned evict=2;
    unsigned i, slot=XIQM_SLOT_COUNT;
    if (xziel_iqm_entities.value==0 || !e || !e->model)
        return false;
    for (i=2;i<XIQM_SLOT_COUNT;i++) {
        if (!strcmp(xiqm_slots[i].model,e->model->name)) {
            slot=i;
            break;
        }
        if (slot==XIQM_SLOT_COUNT && !xiqm_slots[i].model[0])
            slot=i;
    }
    if (slot==XIQM_SLOT_COUNT) {
        slot=evict++;
        if(evict>=XIQM_SLOT_COUNT)evict=2;
    }
    return xiqm_draw_entity(e,slot);
}
