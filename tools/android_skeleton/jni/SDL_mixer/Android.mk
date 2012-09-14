LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := SDL2_mixer
LOCAL_SRC_FILES := libSDL2_mixer.so
include $(PREBUILT_SHARED_LIBRARY)
