LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := SDL_ttf
LOCAL_SRC_FILES := libSDL_ttf.so
include $(PREBUILT_SHARED_LIBRARY)
