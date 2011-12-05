LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE := main

SDL_PATH := ../SDL

LOCAL_C_INCLUDES := \
	$(LOCAL_PATH)/$(SDL_PATH)/include \
	$(LOCAL_PATH)/$(SDL_PATH)/src \
	$(LOCAL_PATH)/../SDL_image \
	$(LOCAL_PATH)/../python \
	$(LOCAL_PATH)/../python/Include

# Add any compilation flags for your project here...
LOCAL_CFLAGS := \
	-DPLAY_MOD

# Add your application source files here...
LOCAL_SRC_FILES := $(SDL_PATH)/src/main/android/SDL_android_main.cpp \
	dp.c jni_glue.cpp

#LOCAL_SHARED_LIBRARIES := SDL SDL_image python2.7

LOCAL_LDLIBS := -lGLESv1_CM -llog -L$(LOCAL_PATH) -L$(LOCAL_PATH)/../SDL -L$(LOCAL_PATH)/../SDL_image -L$(LOCAL_PATH)/../SDL_ttf -L$(LOCAL_PATH)/../python -lz -lSDL -lSDL_image -lSDL_ttf -lpython2.7

include $(BUILD_SHARED_LIBRARY)