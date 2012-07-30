#if ANDROID
#include "android/log.h"
int native_log(int level, char *str) {
    __android_log_print(level, "IGNIFUGA", str );
}
#else
int native_log(int level, char *str) {
    printf(str);
    printf("\n");
    fflush(stdout);
}
#endif