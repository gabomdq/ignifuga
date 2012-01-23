LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := SDL2_image
LOCAL_SRC_FILES := libSDL2_image.so
include $(PREBUILT_SHARED_LIBRARY)
