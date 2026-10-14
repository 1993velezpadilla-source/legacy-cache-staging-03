/* IQM2 transforms. Reference: github.com/lsalzman/iqm. GPL-2.0-or-later */
#ifndef XZIEL_IQM_MATRIX_H
#define XZIEL_IQM_MATRIX_H
#include <math.h>
#include <string.h>
typedef struct { float a[12]; } xzmatrix;
static int xzm_trs(xzmatrix *m, const float t[10]) {
    float n=t[3]*t[3]+t[4]*t[4]+t[5]*t[5]+t[6]*t[6], s,x,y,z,w;
    int i;
    if(!isfinite(n) || n<1e-12f) return 0;
    for(i=0;i<10;i++) if(!isfinite(t[i])) return 0;
    s=1.0f/sqrtf(n); x=t[3]*s; y=t[4]*s; z=t[5]*s; w=t[6]*s;
    m->a[0]=(1-2*(y*y+z*z))*t[7]; m->a[1]=2*(x*y-z*w)*t[8];
    m->a[2]=2*(x*z+y*w)*t[9]; m->a[3]=t[0];
    m->a[4]=2*(x*y+z*w)*t[7]; m->a[5]=(1-2*(x*x+z*z))*t[8];
    m->a[6]=2*(y*z-x*w)*t[9]; m->a[7]=t[1];
    m->a[8]=2*(x*z-y*w)*t[7]; m->a[9]=2*(y*z+x*w)*t[8];
    m->a[10]=(1-2*(x*x+y*y))*t[9]; m->a[11]=t[2];
    return 1;
}
static void xzm_mul(xzmatrix *out, const xzmatrix *a,const xzmatrix *b) {
    xzmatrix v; int r,c;
    for(r=0;r<3;r++) {
       for(c=0;c<3;c++)v.a[4*r+c]=a->a[4*r]*b->a[c]+a->a[4*r+1]*b->a[4+c]+a->a[4*r+2]*b->a[8+c];
       v.a[4*r+3]=a->a[4*r]*b->a[3]+a->a[4*r+1]*b->a[7]+a->a[4*r+2]*b->a[11]+a->a[4*r+3];
    }
    *out=v;
}
static int xzm_inv(xzmatrix *out,const xzmatrix *m) {
    const float *a=m->a;
    float d=a[0]*(a[5]*a[10]-a[6]*a[9])-a[1]*(a[4]*a[10]-a[6]*a[8])+a[2]*(a[4]*a[9]-a[5]*a[8]);
    xzmatrix v;int r;
    if(!isfinite(d)||fabsf(d)<1e-10f)return 0;
    d=1.0f/d;
    v.a[0]=(a[5]*a[10]-a[6]*a[9])*d;v.a[1]=(a[2]*a[9]-a[1]*a[10])*d;v.a[2]=(a[1]*a[6]-a[2]*a[5])*d;
    v.a[4]=(a[6]*a[8]-a[4]*a[10])*d;v.a[5]=(a[0]*a[10]-a[2]*a[8])*d;v.a[6]=(a[2]*a[4]-a[0]*a[6])*d;
    v.a[8]=(a[4]*a[9]-a[5]*a[8])*d;v.a[9]=(a[1]*a[8]-a[0]*a[9])*d;v.a[10]=(a[0]*a[5]-a[1]*a[4])*d;
    for(r=0;r<3;r++)v.a[4*r+3]=-(v.a[4*r]*a[3]+v.a[4*r+1]*a[7]+v.a[4*r+2]*a[11]);
    *out=v;return 1;
}
static void xzm_point(const xzmatrix *m,const float p[3],float o[3]) {
    int i;for(i=0;i<3;i++)o[i]=m->a[4*i]*p[0]+m->a[4*i+1]*p[1]+m->a[4*i+2]*p[2]+m->a[4*i+3];
}
#endif
