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
    int available;
    unsigned triangles, num_batches;
    xiqm_vertex *tri_vertices;
    xiqm_batch *batches;
} xiqm_state;

static xiqm_state xiqm_slots[2];
static xiqm_state *xiqm_active = &xiqm_slots[0];
#define xiqm (*xiqm_active)
static cvar_t xziel_iqm_viewmodels = {"xziel_iqm_viewmodels", "0", true};
static cvar_t xziel_iqm_preview_clip = {"xziel_iqm_preview_clip", "-1", true};

void Xziel_IQM_Init(void) {
    Cvar_RegisterVariable(&xziel_iqm_viewmodels);
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
    xiqm.tri_vertices = NULL;
    xiqm.batches = NULL;
    xiqm.triangles = 0;
    xiqm.num_batches = 0;
    xiqm.available = 0;
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
static xzanim xza_slots[2];
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
    len = strlen(mdlpath);
    if (len < 5 || len + 1 >= sizeof(path) || strcmp(mdlpath + len - 4, ".mdl"))
        return 0;
    memcpy(path, mdlpath, len - 4);
    memcpy(path + len - 4, ".iqm", 5);
    file_len = COM_FOpenFile(path, &f);
    if (file_len < 124 || (unsigned)file_len > XIQM_MAX_BYTES || !f) {
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
    xiqm.triangles = tri_count;
    xiqm.num_batches = mesh_count;
    xiqm.available = 1;
    ok = 1;
    Con_Printf("XZIEL IQM: loaded %s meshes=%u triangles=%u vertices=%u (static stage)\n",
               path, mesh_count, tri_count, vertex_count);
done:
    if (f) fclose(f);
    free(buf);
    free(xyz);
    free(uv);
    if (!ok) {
        Con_Printf("XZIEL IQM: invalid %s, keeping original MDL\n", path);
        xiqm_free();
    }
    return ok;
}
qboolean Xziel_IQM_DrawViewModel(entity_t *e) {
    unsigned i;
    if (xziel_iqm_viewmodels.value == 0 || !e || !e->model)
        return false;
    if (strcmp(xiqm.model, e->model->name)) {
        xiqm_free();
        xiqm_strncpy(xiqm.model, sizeof(xiqm.model), e->model->name);
        xiqm_load(xiqm.model);
    }
    if (!xiqm.available)
        return false;

    glPushMatrix();
    R_RotateForEntity(e, e->scale);
    glEnable(GL_DEPTH_TEST);
    glDisable(GL_BLEND);
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
            }
            if (b->texture < 0) b->texture = -2; /* retry never until model changes */
        }
        if (b->texture >= 0) {
            glEnable(GL_TEXTURE_2D);
            Hyena_BindTexture(b->texture);
        } else {
            glDisable(GL_TEXTURE_2D);
        }
        glDrawArrays(GL_TRIANGLES, (GLint)b->start, (GLsizei)b->count);
    }
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    glDisableClientState(GL_VERTEX_ARRAY);
    glEnable(GL_TEXTURE_2D);
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE);
    glColor4f(1,1,1,1);
    glPopMatrix();
    return true;
}
