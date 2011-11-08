LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := python2.7
LOCAL_SRC_FILES := libpython2.7.so
include $(PREBUILT_SHARED_LIBRARY)
