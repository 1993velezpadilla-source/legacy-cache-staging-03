/* Standalone decoder test on real converted IQM2 fixtures. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
static uint32_t xiqm_u32(const unsigned char *p){
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static float xiqm_f32(const unsigned char *p){
    uint32_t n=xiqm_u32(p);float f;memcpy(&f,&n,4);return f;
}
static int xiqm_span(size_t n,uint32_t offset,uint32_t count,uint32_t stride){
    return stride && offset<=n && count <= (n-offset)/stride;
}
static const char *xiqm_name(const unsigned char *p,unsigned count,unsigned index){
    if(index>=count||!memchr(p+index,0,count-index))return NULL;
    return (const char*)p+index;
}
static void xiqm_strncpy(char *dst,size_t size,const char *src){
    size_t n=strlen(src);if(n>=size)n=size-1;memcpy(dst,src,n);dst[n]=0;
}
#include "xiqm_animation.h"
int main(int argc,char **argv){
    FILE *f;unsigned char *buf;long length;size_t size;int ok;
    xzanim *a;
    unsigned i;
    if(argc!=2)return 2;
    f=fopen(argv[1],"rb");if(!f)return 2;
    if(fseek(f,0,SEEK_END)|| (length=ftell(f))<124 || length>33554432 ||
       fseek(f,0,SEEK_SET)){fclose(f);return 2;}
    size=(size_t)length;buf=(unsigned char*)malloc(size);
    if(!buf){fclose(f);return 2;}
    if(fread(buf,1,size,f)!=size){fclose(f);free(buf);return 2;}
    fclose(f);
    a=(xzanim*)calloc(1,sizeof(*a));
    if(!a){free(buf);return 2;}
    ok=memcmp(buf,"INTERQUAKEMODEL",15)==0&&buf[15]==0&&
        xiqm_u32(buf+16)==2&&xiqm_u32(buf+20)==size;
    if(ok)ok=xza_load(a,buf,size);
    if(ok && a->clips && a->joints) {
        a->weighted=1;
        for(i=0;i<a->clips;i++){
            ok=xza_eval(a,i,0.0f)&&xza_eval(a,i,0.025f);
            if(!ok)break;
            printf("clip=%s joints=%u frames=%u fps=%.2f\n",
                a->clip[i].name,a->joints,a->clip[i].count,a->clip[i].fps);
        }
    }
    printf("IQM_ANIMATION_DECODER_%s\n",ok?"GREEN":"FAIL");
    xza_clear(a);free(a);free(buf);
    return ok?0:1;
}
