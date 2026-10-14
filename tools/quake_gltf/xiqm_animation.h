/* IQM2 skeletal evaluator for optional XZIEL preview; GPL-2.0-or-later */
#ifndef XZIEL_IQM_ANIMATION_H
#define XZIEL_IQM_ANIMATION_H
#include "xiqm_matrix.h"
#define XZA_BONES 128u
#define XZA_CLIPS 64u
#define XZA_FRAMES 8192u
typedef struct {int parent;float v[10];} xzjoint;
typedef struct {int parent;unsigned mask;float offset[10],scale[10];} xzpose;
typedef struct {char name[80];unsigned first,count,flags;float fps;} xzclip;
typedef struct {
 unsigned joints,poses,clips,frames,channels;
 xzjoint joint[XZA_BONES];xzpose pose[XZA_BONES];xzclip clip[XZA_CLIPS];
 xzmatrix inverse[XZA_BONES],skin[XZA_BONES];
 uint16_t *samples;int weighted;
} xzanim;
static void xza_clear(xzanim *a){free(a->samples);memset(a,0,sizeof(*a));}
static int xza_load(xzanim *a,const unsigned char *buf,size_t len){
 unsigned n=xiqm_u32(buf+68), jo=xiqm_u32(buf+72);
 unsigned poses=xiqm_u32(buf+76),po=xiqm_u32(buf+80);
 unsigned clips=xiqm_u32(buf+84),co=xiqm_u32(buf+88);
 unsigned frames=xiqm_u32(buf+92),channels=xiqm_u32(buf+96),fo=xiqm_u32(buf+100);
 unsigned text_count=xiqm_u32(buf+28),to=xiqm_u32(buf+32);
 unsigned i,k,total=0;
 xzmatrix world[XZA_BONES],local;
 if(n>XZA_BONES||poses>XZA_BONES||clips>XZA_CLIPS||frames>XZA_FRAMES||
    channels>1280||!xiqm_span(len,jo,n,48)||
    !xiqm_span(len,po,poses,88)||!xiqm_span(len,co,clips,20)||
    !xiqm_span(len,fo,frames,channels*2)||
    !xiqm_span(len,to,text_count,1))return 0;
 if(!frames||!n||poses!=n||!clips)return 1;
 a->joints=n;a->poses=poses;a->clips=clips;a->frames=frames;a->channels=channels;
 for(i=0;i<n;i++){
    const unsigned char *p=buf+jo+i*48;
    xzjoint *j=&a->joint[i];
    j->parent=(int32_t)xiqm_u32(p+4);
    if(j->parent>=(int)i||j->parent< -1)return 0;
    for(k=0;k<10;k++)j->v[k]=xiqm_f32(p+8+4*k);
    if(!xzm_trs(&local,j->v))return 0;
    if(j->parent>=0)xzm_mul(&world[i],&world[j->parent],&local);
    else world[i]=local;
    if(!xzm_inv(&a->inverse[i],&world[i]))return 0;
 }
