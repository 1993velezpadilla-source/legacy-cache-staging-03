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
