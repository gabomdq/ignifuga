/*
Copyright (c) 2010,2011, Gabriel Jacobo
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Altered source versions must be plainly marked as such, and must not be
      misrepresented as being the original software.
    * Neither the name of Gabriel Jacobo, MDQ Incorporeo, Ignifuga Game Engine
      nor the names of its contributors may be used to endorse or promote
      products derived from this software without specific prior written permission.
    * You must NOT, under ANY CIRCUMSTANCES, remove, modify or alter in any way
      the duration, code functionality and graphic or audio material related to
      the "splash screen", which should always be the first screen shown by the
      derived work and which should ALWAYS state the Ignifuga Game Engine name,
      original author's URL and company logo.

THIS LICENSE AGREEMENT WILL AUTOMATICALLY TERMINATE UPON A MATERIAL BREACH OF ITS
TERMS AND CONDITIONS

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL GABRIEL JACOBO NOR MDQ INCORPOREO NOR THE CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include <jni.h>
#include "SDL_config.h"
#include "SDL_stdinc.h"
/* Include the SDL main definition header */
#include "SDL_main.h"
//#include "core/android/SDL_android.h"
//#include "video/android/SDL_androidvideo.h"
//#include "video/android/SDL_androidkeyboard.h"
//#include "video/android/SDL_androidtouch.h"
//#include "events/SDL_events_c.h"

//static float fLastAccelerometer[3];
extern "C" {
    void Java_org_libsdl_app_SDLActivity_nativeRunAudioThread(JNIEnv* env, jclass cls);
    void Java_org_libsdl_app_SDLActivity_onNativeResize(
                                    JNIEnv* env, jclass jcls,
                                    jint width, jint height, jint format);
    void Java_org_libsdl_app_SDLActivity_onNativeKeyDown(
                                    JNIEnv* env, jclass jcls, jint keycode);
    void Java_org_libsdl_app_SDLActivity_onNativeKeyUp(
                                    JNIEnv* env, jclass jcls, jint keycode);
    void Java_org_libsdl_app_SDLActivity_onNativeTouch(
                                    JNIEnv* env, jclass jcls,
                                    jint touch_device_id_in, jint pointer_finger_id_in,
                                    jint action, jfloat x, jfloat y, jfloat p);
    void Java_org_libsdl_app_SDLActivity_onNativeAccel(
                                    JNIEnv* env, jclass jcls,
                                    jfloat x, jfloat y, jfloat z);
    void Java_org_libsdl_app_SDLActivity_nativeQuit(
                                    JNIEnv* env, jclass cls);
    void Java_org_libsdl_app_SDLActivity_nativeRunAudioThread(
                                    JNIEnv* env, jclass cls);
    void Java_org_libsdl_app_SDLActivity_nativeInit(JNIEnv* env, jclass cls, jobject obj);
    void Java_org_libsdl_app_SDLActivity_nativePause(JNIEnv* env, jclass cls, jobject obj);
    void Java_org_libsdl_app_SDLActivity_nativeResume(JNIEnv* env, jclass cls, jobject obj);
    void Java_org_libsdl_app_SDLActivity_onNativeOffsetsChanged(
                                        JNIEnv* env, jclass cls, jfloat x, jfloat y);
    jint JNI_OnLoad(JavaVM* vm, void* reserved);
    void SDL_Android_Init(JNIEnv* env, jclass cls);
};

// Resize
extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_onNativeResize(
                                    JNIEnv* env, jclass jcls,
                                    jint width, jint height, jint format)
{
    Java_org_libsdl_app_SDLActivity_onNativeResize(env, jcls, width, height, format);
}

// Keydown
extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_onNativeKeyDown(
                                    JNIEnv* env, jclass jcls, jint keycode)
{
    Java_org_libsdl_app_SDLActivity_onNativeKeyDown(env, jcls, keycode);
}

// Keyup
extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_onNativeKeyUp(
                                    JNIEnv* env, jclass jcls, jint keycode)
{
    Java_org_libsdl_app_SDLActivity_onNativeKeyUp(env, jcls, keycode);
}

// Touch
extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_onNativeTouch(
                                    JNIEnv* env, jclass jcls,
                                    jint touch_device_id_in, jint pointer_finger_id_in,
                                    jint action, jfloat x, jfloat y, jfloat p)
{
    Java_org_libsdl_app_SDLActivity_onNativeTouch(env, jcls, touch_device_id_in, pointer_finger_id_in, action, x, y, p);
}

// Accelerometer
extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_onNativeAccel(
                                    JNIEnv* env, jclass jcls,
                                    jfloat x, jfloat y, jfloat z)
{
     Java_org_libsdl_app_SDLActivity_onNativeAccel(env, jcls, x, y, z);
}

// Quit
extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_nativeQuit(
                                    JNIEnv* env, jclass cls)
{    
    Java_org_libsdl_app_SDLActivity_nativeQuit(env, cls);
}

extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_nativeRunAudioThread(
                                    JNIEnv* env, jclass cls)
{
    Java_org_libsdl_app_SDLActivity_nativeRunAudioThread(env, cls);
}

extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_nativeInit(JNIEnv* env, jclass cls, jobject obj) {
    //Java_org_libsdl_app_SDLActivity_nativeInit(env, cls, obj);
     /* This interface could expand with ABI negotiation, calbacks, etc. */
    SDL_Android_Init(env, cls);

    /* Run the application code! */
    int status;
    char *argv[2];
    argv[0] = strdup("SDL_app");
    argv[1] = NULL;
    status = SDL_main(1, argv);

    // Don't issue exit!
}

extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_nativePause(JNIEnv* env, jclass cls, jobject obj) {
    Java_org_libsdl_app_SDLActivity_nativePause(env, cls, obj);
}

extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_nativeResume(JNIEnv* env, jclass cls, jobject obj) {
    Java_org_libsdl_app_SDLActivity_nativeResume(env, cls, obj);
}

extern "C" void Java_[[PROJECT_NAME]]_SDLActivity_onNativeOffsetsChanged(JNIEnv* env, jclass cls, jfloat x, jfloat y) {
    Java_org_libsdl_app_SDLActivity_onNativeOffsetsChanged(env, cls, x, y);
}