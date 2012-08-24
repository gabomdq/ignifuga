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

package [[PROJECT_NAME]];

import javax.microedition.khronos.egl.EGL10;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.egl.EGLContext;
import javax.microedition.khronos.opengles.GL10;
import javax.microedition.khronos.egl.*;

import android.app.*;
import android.content.*;
import android.view.*;
import android.view.inputmethod.InputMethodManager;
import android.os.*;
import android.util.Log;
import android.graphics.*;
import android.text.method.*;
import android.text.*;
import android.media.*;
import android.hardware.*;
import android.content.*;
import android.service.wallpaper.WallpaperService;
import java.lang.*;


/**
    SDL Activity
*/
public class SDLActivity extends WallpaperService {

    // Main components
    private static SDLActivity mSingleton;
    private static SDLEngine mEngine;

    // Audio
    private static Thread mAudioThread;
    private static AudioTrack mAudioTrack;

    // Load the .so
    static {
        System.loadLibrary("SDL2");
        System.loadLibrary("SDL2_image");
        System.loadLibrary("SDL2_ttf");
        //System.loadLibrary("mikmod");
        //System.loadLibrary("SDL2_mixer");
        System.loadLibrary("python2.7");
        System.loadLibrary("main");
    }

    @Override
    public void onCreate() {
        super.onCreate();
        mSingleton = this;
        // Set up the surface
        /*mSurface = new SDLSurface(getApplication());
        setContentView(mSurface);
        SurfaceHolder holder = mSurface.getHolder();*/
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        //Log.v("SDL", "onDestroy()");

        // Send a quit message to the application

        SDLActivity.nativeQuit();
        //Log.v("SDL", "Waiting for SDL thread");
        // Now wait for the SDL thread to quit
        if (mEngine.mSDLThread != null) {
            try {
                mEngine.mSDLThread.join();
            } catch(Exception e) {
                //Log.v("SDL", "Problem stopping thread: " + e);
            }
            mEngine.mSDLThread = null;

            //Log.v("SDL", "Finished waiting for SDL thread");
        }

    }

    /*protected void onPause(){
        //Log.v("SDL", "SDLActivity onPause");
        SDLActivity.nativePause();
    }

    protected void onResume(){
        //Log.v("SDL", "SDLActivity onResume");
        // Don't call SDLActivity.nativeResume(); here, it will be called via SDLSurface::surfaceChanged->SDLActivity::startApp
    }*/

    @Override
    public Engine onCreateEngine() {
        //Log.v("SDL", "onCreateEngine()");
        if (mEngine != null){
            //Log.v("SDL", "Waiting for SDL thread");
            if (mEngine.mSDLThread != null) {
                SDLActivity.nativeQuit();
                try {
                    mEngine.mSDLThread.join();
                } catch(Exception e) {
                    //Log.v("SDL", "Problem stopping thread: " + e);
                }
            }
            //Log.v("SDL", "SDL thread finished");
        }
        //Log.v("SDL", "Creating SDL Engine");
        mEngine = new SDLEngine();
        return mEngine;
    }

    // Messages from the SDLMain thread
    static final int COMMAND_CHANGE_TITLE = 1;
    static final int COMMAND_KEYBOARD_SHOW = 2;

    // Handler for the messages
    Handler commandHandler = new Handler() {
        public void handleMessage(Message msg) {
            switch (msg.arg1) {
            case COMMAND_CHANGE_TITLE:
                 setTitle((String)msg.obj);
                break;
            case COMMAND_KEYBOARD_SHOW:
                InputMethodManager manager = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
                if (manager != null) {
                    switch (((Integer)msg.obj).intValue()) {
                    case 0:
                        manager.hideSoftInputFromWindow(mSurface.getWindowToken(), 0);
                        break;
                    case 1:
                        manager.showSoftInput(mSurface, 0);
                        break;
                    case 2:
                        manager.toggleSoftInputFromWindow(mSurface.getWindowToken(), 0, 0);
                        break;
                    }
                }
               break;
        }
    };

    // Send a message from the SDLMain thread
    void sendCommand(int command, Object data) {
        Message msg = commandHandler.obtainMessage();
        msg.arg1 = command;
        msg.obj = data;
        commandHandler.sendMessage(msg);
    }

    // C functions we call
    public static native void nativeInit();
    public static native void nativeQuit();
    public static native void nativePause();
    public static native void nativeResume();
    public static native void onNativeResize(int x, int y, int format);
    public static native void onNativeKeyDown(int keycode);
    public static native void onNativeKeyUp(int keycode);
    public static native void onNativeTouch(int touchDevId, int pointerFingerId,
                                            int action, float x, 
                                            float y, float p);
    public static native void onNativeAccel(float x, float y, float z);
    public static native void onNativeOffsetsChanged(float x, float y);
    public static native void nativeRunAudioThread();


    // Java functions called from C

    public static boolean createGLContext(int majorVersion, int minorVersion) {
        return mEngine.initEGL(majorVersion, minorVersion);
    }

    public static void flipBuffers() {
        mEngine.flipEGL();
    }

    public static void setActivityTitle(String title) {
        // Called from SDLMain() thread and can't directly affect the view
        mSingleton.sendCommand(COMMAND_CHANGE_TITLE, title);
    }

    public static void sendMessage(int command, int param) {
        mSingleton.sendCommand(command, Integer.valueOf(param));
    }

    public static Context getContext() {
        return mSingleton;
    }

    // Audio
    private static Object buf;
    
    public static Object audioInit(int sampleRate, boolean is16Bit, boolean isStereo, int desiredFrames) {
        int channelConfig = isStereo ? AudioFormat.CHANNEL_CONFIGURATION_STEREO : AudioFormat.CHANNEL_CONFIGURATION_MONO;
        int audioFormat = is16Bit ? AudioFormat.ENCODING_PCM_16BIT : AudioFormat.ENCODING_PCM_8BIT;
        int frameSize = (isStereo ? 2 : 1) * (is16Bit ? 2 : 1);
        
        //Log.v("SDL", "SDL audio: wanted " + (isStereo ? "stereo" : "mono") + " " + (is16Bit ? "16-bit" : "8-bit") + " " + ((float)sampleRate / 1000f) + "kHz, " + desiredFrames + " frames buffer");
        
        // Let the user pick a larger buffer if they really want -- but ye
        // gods they probably shouldn't, the minimums are horrifyingly high
        // latency already
        desiredFrames = Math.max(desiredFrames, (AudioTrack.getMinBufferSize(sampleRate, channelConfig, audioFormat) + frameSize - 1) / frameSize);
        
        mAudioTrack = new AudioTrack(AudioManager.STREAM_MUSIC, sampleRate,
                channelConfig, audioFormat, desiredFrames * frameSize, AudioTrack.MODE_STREAM);
        
        audioStartThread();
        
        //Log.v("SDL", "SDL audio: got " + ((mAudioTrack.getChannelCount() >= 2) ? "stereo" : "mono") + " " + ((mAudioTrack.getAudioFormat() == AudioFormat.ENCODING_PCM_16BIT) ? "16-bit" : "8-bit") + " " + ((float)mAudioTrack.getSampleRate() / 1000f) + "kHz, " + desiredFrames + " frames buffer");
        
        if (is16Bit) {
            buf = new short[desiredFrames * (isStereo ? 2 : 1)];
        } else {
            buf = new byte[desiredFrames * (isStereo ? 2 : 1)]; 
        }
        return buf;
    }
    
    public static void audioStartThread() {
        mAudioThread = new Thread(new Runnable() {
            public void run() {
                mAudioTrack.play();
                nativeRunAudioThread();
            }
        });
        
        // I'd take REALTIME if I could get it!
        mAudioThread.setPriority(Thread.MAX_PRIORITY);
        mAudioThread.start();
    }
    
    public static void audioWriteShortBuffer(short[] buffer) {
        for (int i = 0; i < buffer.length; ) {
            int result = mAudioTrack.write(buffer, i, buffer.length - i);
            if (result > 0) {
                i += result;
            } else if (result == 0) {
                try {
                    Thread.sleep(1);
                } catch(InterruptedException e) {
                    // Nom nom
                }
            } else {
                //Log.w("SDL", "SDL audio: error return from write(short)");
                return;
            }
        }
    }
    
    public static void audioWriteByteBuffer(byte[] buffer) {
        for (int i = 0; i < buffer.length; ) {
            int result = mAudioTrack.write(buffer, i, buffer.length - i);
            if (result > 0) {
                i += result;
            } else if (result == 0) {
                try {
                    Thread.sleep(1);
                } catch(InterruptedException e) {
                    // Nom nom
                }
            } else {
                //Log.w("SDL", "SDL audio: error return from write(short)");
                return;
            }
        }
    }

    public static void audioQuit() {
        if (mAudioThread != null) {
            try {
                mAudioThread.join();
            } catch(Exception e) {
                //Log.v("SDL", "Problem stopping audio thread: " + e);
            }
            mAudioThread = null;

            //Log.v("SDL", "Finished waiting for audio thread");
        }

        if (mAudioTrack != null) {
            mAudioTrack.stop();
            mAudioTrack = null;
        }
    }


    /**
        SDLEngine
    */
    class SDLEngine extends Engine {//SurfaceView implements SurfaceHolder.Callback, View.OnKeyListener, View.OnTouchListener, SensorEventListener

        // This is what SDL runs in. It invokes SDL_main(), eventually
        public Thread mSDLThread;
        private SurfaceHolder mHolder;

        // EGL private objects
        private EGLContext  mEGLContext;
        private EGLSurface  mEGLSurface;
        private EGLDisplay  mEGLDisplay;
        private EGLConfig   mEGLConfig;
        private int mGLMajor, mGLMinor;

        // Keep track of the surface size to normalize touch events
        private float mWidth, mHeight;

        // Sensors
        //private static SensorManager mSensorManager;

        // Startup
        public SDLEngine() {
            super();

            // Some arbitrary defaults to avoid a potential division by zero
            mWidth = 1.0;
            mHeight = 1.0;
            
            /*getHolder().addCallback(this);

            setFocusable(true);
            setFocusableInTouchMode(true);
            requestFocus();
            setOnKeyListener(this);
            setOnTouchListener(this);*/

            //mSensorManager = (SensorManager)context.getSystemService("sensor");
        }

        /*@Override
        public void onResume() {
            super.onResume();
            //Log.v("SDL", "SDLEngine onResume");
        }

        @Override
        public void onPause() {
            super.onPause();
            //Log.v("SDL", "SDLEngine onPause");
        }

        @Override
        public void onDestroy() {
            super.onDestroy();
            //Log.v("SDL", "SDLEngine onDestroy");
        }*/

        @Override
        public void onVisibilityChanged(boolean visible) {
            //Log.v("SDL", "onVisibilityChanged " + visible);
            if (visible) {
                SDLActivity.nativeResume();
            } else {
                SDLActivity.nativePause();
            }
        }

        // Called when we have a valid drawing surface
        @Override
        public void onSurfaceCreated(SurfaceHolder holder) {
            super.onSurfaceCreated(holder);
            mHolder = holder;
            //Log.v("SDL", "surfaceCreated() " + holder);
            mHolder.setType(SurfaceHolder.SURFACE_TYPE_GPU);
            enableSensor(Sensor.TYPE_ACCELEROMETER, true);
        }

        // Called when we lose the surface
        @Override
        public void onSurfaceDestroyed(SurfaceHolder holder) {
            if (holder == SDLActivity.mEngine.mHolder) {
                super.onSurfaceDestroyed(holder);
                //Log.v("SDL", "surfaceDestroyed() " + holder + " " + mHolder);
                SDLActivity.nativePause();
                enableSensor(Sensor.TYPE_ACCELEROMETER, false);
            }
        }

        // Called when the surface is resized
        @Override
        public void onSurfaceChanged(SurfaceHolder holder,
                                   int format, int width, int height) {
            super.onSurfaceChanged(holder, format, width, height);
            //Log.v("SDL", "surfaceChanged()" + holder);

            int sdlFormat = 0x85151002; // SDL_PIXELFORMAT_RGB565 by default
            switch (format) {
            case PixelFormat.A_8:
                //Log.v("SDL", "pixel format A_8");
                break;
            case PixelFormat.LA_88:
                //Log.v("SDL", "pixel format LA_88");
                break;
            case PixelFormat.L_8:
                //Log.v("SDL", "pixel format L_8");
                break;
            case PixelFormat.RGBA_4444:
                //Log.v("SDL", "pixel format RGBA_4444");
                sdlFormat = 0x85421002; // SDL_PIXELFORMAT_RGBA4444
                break;
            case PixelFormat.RGBA_5551:
                //Log.v("SDL", "pixel format RGBA_5551");
                sdlFormat = 0x85441002; // SDL_PIXELFORMAT_RGBA5551
                break;
            case PixelFormat.RGBA_8888:
                //Log.v("SDL", "pixel format RGBA_8888");
                sdlFormat = 0x86462004; // SDL_PIXELFORMAT_RGBA8888
                break;
            case PixelFormat.RGBX_8888:
                //Log.v("SDL", "pixel format RGBX_8888");
                sdlFormat = 0x86262004; // SDL_PIXELFORMAT_RGBX8888
                break;
            case PixelFormat.RGB_332:
                //Log.v("SDL", "pixel format RGB_332");
                sdlFormat = 0x84110801; // SDL_PIXELFORMAT_RGB332
                break;
            case PixelFormat.RGB_565:
                //Log.v("SDL", "pixel format RGB_565");
                sdlFormat = 0x85151002; // SDL_PIXELFORMAT_RGB565
                break;
            case PixelFormat.RGB_888:
                //Log.v("SDL", "pixel format RGB_888");
                // Not sure this is right, maybe SDL_PIXELFORMAT_RGB24 instead?
                sdlFormat = 0x86161804; // SDL_PIXELFORMAT_RGB888
                break;
            default:
                //Log.v("SDL", "pixel format unknown " + format);
                break;
            }
            mWidth = (float) width;
            mHeight = (float) height;
            SDLActivity.onNativeResize(width, height, sdlFormat);
            //Log.v("SDL", "Window size:" + width + "x"+height);

            // Now start up the C app thread
            if (mSDLThread == null) {
                //Log.v("SDL", "Starting SDLThread");
                mSDLThread = new Thread(new SDLMain(), "SDLThread");
                mSDLThread.start();
            }
            else {
                //Log.v("SDL", "SDLThread already exists");
                SDLActivity.nativeResume();
            }
        }

        // unused
        public void onDraw(Canvas canvas) {}


        // EGL functions
        public boolean initEGL(int majorVersion, int minorVersion) {
            if (mEGLContext == null) {
                //Log.v("SDL", "Starting up OpenGL ES " + majorVersion + "." + minorVersion);

                try {
                    EGL10 egl = (EGL10)EGLContext.getEGL();

                    EGLDisplay dpy = egl.eglGetDisplay(EGL10.EGL_DEFAULT_DISPLAY);

                    int[] version = new int[2];
                    egl.eglInitialize(dpy, version);

                    int EGL_OPENGL_ES_BIT = 1;
                    int EGL_OPENGL_ES2_BIT = 4;
                    int renderableType = 0;
                    if (majorVersion == 2) {
                        renderableType = EGL_OPENGL_ES2_BIT;
                    } else if (majorVersion == 1) {
                        renderableType = EGL_OPENGL_ES_BIT;
                    }
                    int[] configSpec = {
                        //EGL10.EGL_DEPTH_SIZE,   16,
                        EGL10.EGL_RENDERABLE_TYPE, renderableType,
                        EGL10.EGL_NONE
                    };
                    EGLConfig[] configs = new EGLConfig[1];
                    int[] num_config = new int[1];
                    if (!egl.eglChooseConfig(dpy, configSpec, configs, 1, num_config) || num_config[0] == 0) {
                        Log.e("SDL", "No EGL config available");
                        return false;
                    }
                    EGLConfig config = configs[0];
                    mEGLDisplay = dpy;
                    mEGLConfig = config;
                    mGLMajor = majorVersion;
                    mGLMinor = minorVersion;

                    createEGLSurface();
                } catch(Exception e) {
                    Log.v("SDL", e + "");
                    for (StackTraceElement s : e.getStackTrace()) {
                        Log.v("SDL", s.toString());
                    }
                }
            }
            else createEGLSurface();

            return true;
        }

        public boolean createEGLContext() {
            EGL10 egl = (EGL10)EGLContext.getEGL();
            int EGL_CONTEXT_CLIENT_VERSION=0x3098;
            int contextAttrs[] = new int[] { EGL_CONTEXT_CLIENT_VERSION, mGLMajor, EGL10.EGL_NONE };
            EGLContext ctx = egl.eglCreateContext(mEGLDisplay, mEGLConfig, EGL10.EGL_NO_CONTEXT, contextAttrs);

            if (ctx == EGL10.EGL_NO_CONTEXT) {
                Log.e("SDL", "Couldn't create context");
                return false;
            }
            mEGLContext = ctx;
            return true;
        }

        public boolean createEGLSurface() {
            if (mEGLDisplay != null && mEGLConfig != null && mHolder != null) {
                EGL10 egl = (EGL10)EGLContext.getEGL();
                EGLSurface surface = egl.eglCreateWindowSurface(mEGLDisplay, mEGLConfig, mHolder, null);
                if (surface == EGL10.EGL_NO_SURFACE) {
                    Log.e("SDL", "Couldn't create surface");
                    return false;
                }

                if (mEGLContext == null) createEGLContext();

                if (egl.eglGetCurrentContext() != SDLActivity.mEGLContext) {
                    if (!egl.eglMakeCurrent(mEGLDisplay, surface, surface, mEGLContext)) {
                        Log.e("SDL", "Couldn't make context current");
                        createEGLContext();
                        if (!egl.eglMakeCurrent(mEGLDisplay, surface, surface, mEGLContext)) {
                            return false;
                        }
                    }
                }
                mEGLSurface = surface;
                return true;
            }
            return false;
        }

        // EGL buffer flip
        public void flipEGL() {
            try {
                EGL10 egl = (EGL10)EGLContext.getEGL();

                egl.eglWaitNative(EGL10.EGL_CORE_NATIVE_ENGINE, null);

                // drawing here

                egl.eglWaitGL();

                egl.eglSwapBuffers(mEGLDisplay, mEGLSurface);


            } catch(Exception e) {
                Log.v("SDL", "flipEGL(): " + e);
                for (StackTraceElement s : e.getStackTrace()) {
                    Log.v("SDL", s.toString());
                }
            }
        }

        // Key events
        public boolean onKey(View  v, int keyCode, KeyEvent event) {

            if (event.getAction() == KeyEvent.ACTION_DOWN) {
                //Log.v("SDL", "key down: " + keyCode);
                SDLActivity.onNativeKeyDown(keyCode);
                return true;
            }
            else if (event.getAction() == KeyEvent.ACTION_UP) {
                //Log.v("SDL", "key up: " + keyCode);
                SDLActivity.onNativeKeyUp(keyCode);
                return true;
            }

            return false;
        }

        @Override
        public void onOffsetsChanged(float xOffset, float yOffset, float xStep, float yStep, int xPixels, int yPixels) {
            //Log.v("SDL", "offsetsChanged " + xOffset + " " + yOffset + " " + xStep + " " + yStep + " " + xPixels + " " + yPixels);
            SDLActivity.onNativeOffsetsChanged(xOffset, yOffset);
        }

        @Override
        public void onTouchEvent(MotionEvent event) {
             final int touchDevId = event.getDeviceId();
             final int pointerCount = event.getPointerCount();
             // touchId, pointerId, action, x, y, pressure
             int actionPointerIndex = event.getActionIndex();
             int pointerFingerId = event.getPointerId(actionPointerIndex);
             int action = event.getActionMasked();

             float x = event.getX(actionPointerIndex) / mWidth;
             float y = event.getY(actionPointerIndex) / mHeight;
             float p = event.getPressure(actionPointerIndex);

             if (action == MotionEvent.ACTION_MOVE && pointerCount > 1) {
                // TODO send motion to every pointer if its position has
                // changed since prev event.
                for (int i = 0; i < pointerCount; i++) {
                    pointerFingerId = event.getPointerId(i);
                    x = event.getX(i) / mWidth;
                    y = event.getY(i) / mHeight;
                    p = event.getPressure(i);
                    SDLActivity.onNativeTouch(touchDevId, pointerFingerId, action, x, y, p);
                }
             } else {
                SDLActivity.onNativeTouch(touchDevId, pointerFingerId, action, x, y, p);
             }
       }

        // Sensor events
        public void enableSensor(int sensortype, boolean enabled) {
            // TODO: This uses getDefaultSensor - what if we have >1 accels?
            /*if (enabled) {
                mSensorManager.registerListener(this,
                                mSensorManager.getDefaultSensor(sensortype),
                                SensorManager.SENSOR_DELAY_GAME, null);
            } else {
                mSensorManager.unregisterListener(this,
                                mSensorManager.getDefaultSensor(sensortype));
            }*/
        }

        public void onAccuracyChanged(Sensor sensor, int accuracy) {
            // TODO
        }

        public void onSensorChanged(SensorEvent event) {
            if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
                SDLActivity.onNativeAccel(event.values[0],
                                          event.values[1],
                                          event.values[2]);
            }
        }

    }

}

/**
    Simple nativeInit() runnable
*/
class SDLMain implements Runnable {
    public void run() {
        // Runs SDL_main()
        //Log.v("SDL", "SDL runnable starts: " + this);
        SDLActivity.nativeInit();

        //Log.v("SDL", "SDL runnable terminated " + this );
    }
}




