/*
 * Copyright (c) 2010-2012, Gabriel Jacobo
 * All rights reserved.
 * Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
 * whose terms are available in the LICENSE file or at http://www.ignifuga.org/license
 *
 */

#include "backends/sdl/RocketGlue.hpp"
#include "backends/sdl/RocketGlueGL.hpp"
#include "backends/sdl/RocketGlueGLES.hpp"
#include "backends/sdl/RocketGlueGLES2.hpp"

#include <Rocket/Core/Python/ElementDocumentWrapper.h>

#if defined(__ANDROID__)
#include <android/log.h>
#endif

#if defined(__APPLE_CC__) || defined(BSD)
#include <TargetConditionals.h>
#endif

static RocketSDLSystemInterface *rocketSys=NULL;
static RocketSDLFileInterface *rocketFile=NULL;

#if SDL_VIDEO_RENDER_OGL
static RocketSDLRenderInterfaceOpenGL *rocketRenderGL=NULL;
#endif
#if SDL_VIDEO_RENDER_OGL_ES
static RocketSDLRenderInterfaceOpenGLES *rocketRenderGLES=NULL;
#endif
#if SDL_VIDEO_RENDER_OGL_ES2
static RocketSDLRenderInterfaceOpenGLES2 *rocketRenderGLES2=NULL;
#endif

Rocket::Core::Context* RocketInit(SDL_Renderer *renderer, SDL_Window *window)
{
	/* Setup rocket */
	bool renderSystemReady = false;
	rocketSys = new RocketSDLSystemInterface();
	rocketFile = new RocketSDLFileInterface();

	Rocket::Core::SetSystemInterface( rocketSys );
	Rocket::Core::SetFileInterface( rocketFile );
	SDL_RendererInfo render_info;
	SDL_GetRendererInfo(renderer, &render_info);

	#if SDL_VIDEO_RENDER_OGL
	if(strcmp("opengl", render_info.name)==0) {
        rocketRenderGL = new RocketSDLRenderInterfaceOpenGL(renderer, window);
        Rocket::Core::SetRenderInterface( rocketRenderGL );
        renderSystemReady = true;
    }
    #endif

    #if SDL_VIDEO_RENDER_OGL_ES
    if(!renderSystemReady && strcmp("opengles", render_info.name)==0) {
        rocketRenderGLES = new RocketSDLRenderInterfaceOpenGLES(renderer, window);
        Rocket::Core::SetRenderInterface( rocketRenderGLES );
        renderSystemReady = true;
    }
    #endif

    #if SDL_VIDEO_RENDER_OGL_ES2
    if(!renderSystemReady && strcmp("opengles2", render_info.name)==0) {
        rocketRenderGLES2 = new RocketSDLRenderInterfaceOpenGLES2(renderer, window);
        Rocket::Core::SetRenderInterface( rocketRenderGLES2 );
        renderSystemReady = true;
    }
    #endif

    if (!renderSystemReady) {
        #if defined(ANDROID)
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "ERROR WHILE CREATING RENDERER FOR ROCKET");
        #else
        printf("ERROR WHILE CREATING RENDERER FOR ROCKET\n");
        fflush(stdout);
        #endif
        return NULL;
    }

	Rocket::Core::Initialise();
	Rocket::Controls::Initialise();

	int width, height;
	SDL_GetWindowSize(window, &width, &height);

	Rocket::Core::Context* rocketContext = Rocket::Core::CreateContext( "main", Rocket::Core::Vector2i(width, height) );

	return rocketContext;
}


void RocketFree(Rocket::Core::Context *mainCtx) {
	mainCtx->RemoveReference();
	Rocket::Core::Shutdown();
	if (rocketSys) {
	    delete rocketSys;
	    rocketSys = NULL;
	}
	#if SDL_VIDEO_RENDER_OGL
    if (rocketRenderGL) {
   	    delete rocketRenderGL;
   	    rocketRenderGL = NULL;
   	}
    #endif

    #if SDL_VIDEO_RENDER_OGLES
    if (rocketRenderGLES) {
   	    delete rocketRenderGLES;
   	    rocketRenderGLES = NULL;
   	}
    #endif

    #if SDL_VIDEO_RENDER_OGLES2
    if (rocketRenderGLES2) {
   	    delete rocketRenderGLES2;
   	    rocketRenderGLES2 = NULL;
   	}
    #endif

}

void InjectRocket( Rocket::Core::Context* context, SDL_Event& event )
	{
	using Rocket::Core::Input::KeyIdentifier;
	switch( event.type )
		{
		case SDL_KEYDOWN:
			{			
			SDL_Keycode sdlkey = event.key.keysym.sym;
			int key = SDLKeyToRocketInput(sdlkey);
			context->ProcessKeyDown( KeyIdentifier( key ), RocketConvertSDLmod( event.key.keysym.mod ) );
			}
			break;
		case SDL_TEXTINPUT:
		    {
		    SDL_TextInputEvent *tiev = (SDL_TextInputEvent *)&event;
		    /*if( c != 0 && c != 8 )*/ context->ProcessTextInput(Rocket::Core::String(tiev->text));
		    }
		    break;

		case SDL_KEYUP:
			context->ProcessKeyUp( KeyIdentifier( event.key.keysym.scancode ), RocketConvertSDLmod( event.key.keysym.mod ) );
			break;

        #if defined(__ANDROID__) || ((defined(__APPLE_CC__) || defined(BSD)) && (TARGET_OS_IPHONE == 1 || TARGET_IPHONE_SIMULATOR == 1))
        /*
         * Android or iOS should handle touches
         * We use the first finger press as a mouse pointer linked to mouse button 0 (left button)
         *
         */
        case SDL_FINGERMOTION:
            if (event.tfinger.fingerId == 0) {
                const Rocket::Core::Vector2i& size = context->GetDimensions();
                int x = event.tfinger.x * size.x / 32768;
                int y = event.tfinger.y * size.y / 32768;
                context->ProcessMouseMove( x, y, Rocket::Core::Input::KeyModifier(0) );
            }
            break;
        case SDL_FINGERDOWN:
            if (event.tfinger.fingerId == 0) {
                const Rocket::Core::Vector2i& size = context->GetDimensions();
                int x = event.tfinger.x * size.x / 32768;
                int y = event.tfinger.y * size.y / 32768;
                context->ProcessMouseMove( x, y, Rocket::Core::Input::KeyModifier(0) );
                context->ProcessMouseButtonDown( 0, Rocket::Core::Input::KeyModifier(0) );
            }
            break;
        case SDL_FINGERUP:
            if (event.tfinger.fingerId == 0) {
                const Rocket::Core::Vector2i& size = context->GetDimensions();
                int x = event.tfinger.x * size.x / 32768;
                int y = event.tfinger.y * size.y / 32768;
                context->ProcessMouseMove( x, y, Rocket::Core::Input::KeyModifier(0) );
                context->ProcessMouseButtonUp( 0, Rocket::Core::Input::KeyModifier(0) );
            }
            break;
        #else
        // Desktop systems handle mouse events
		case SDL_MOUSEMOTION:
			context->ProcessMouseMove( event.motion.x, event.motion.y, RocketConvertSDLmod( SDL_GetModState() ) );
			break;
		case SDL_MOUSEBUTTONDOWN:
			context->ProcessMouseButtonDown( RocketConvertSDLButton(event.button.button), RocketConvertSDLmod( SDL_GetModState() ) );
			break;
		case SDL_MOUSEBUTTONUP:
			context->ProcessMouseButtonUp( RocketConvertSDLButton(event.button.button), RocketConvertSDLmod( SDL_GetModState() ) );
			break;
		case SDL_MOUSEWHEEL:
		    context->ProcessMouseWheel(event.wheel.y, RocketConvertSDLmod( SDL_GetModState() ) );
		    break;

		#endif // defined(__ANDROID__) || ((defined(__APPLE_CC__) || defined(BSD)) && (TARGET_OS_IPHONE == 1 || TARGET_IPHONE_SIMULATOR == 1))

		default:
        	break;
		}
	}

int SDLKeyToRocketInput(SDL_Keycode sdlkey)
{
	using namespace Rocket::Core::Input;


	switch(sdlkey) {
        case SDLK_UNKNOWN:
            return KI_UNKNOWN;
            break;
        case SDLK_SPACE:
            return KI_SPACE;
            break;
        case SDLK_0:
            return KI_0;
            break;
        case SDLK_1:
            return KI_1;
            break;
        case SDLK_2:
            return KI_2;
            break;
        case SDLK_3:
            return KI_3;
            break;
        case SDLK_4:
            return KI_4;
            break;
        case SDLK_5:
            return KI_5;
            break;
        case SDLK_6:
            return KI_6;
            break;
        case SDLK_7:
            return KI_7;
            break;
        case SDLK_8:
            return KI_8;
            break;
        case SDLK_9:
            return KI_9;
            break;
        case SDLK_a:
            return KI_A;
            break;
        case SDLK_b:
            return KI_B;
            break;
        case SDLK_c:
            return KI_C;
            break;
        case SDLK_d:
            return KI_D;
            break;
        case SDLK_e:
            return KI_E;
            break;
        case SDLK_f:
            return KI_F;
            break;
        case SDLK_g:
            return KI_G;
            break;
        case SDLK_h:
            return KI_H;
            break;
        case SDLK_i:
            return KI_I;
            break;
        case SDLK_j:
            return KI_J;
            break;
        case SDLK_k:
            return KI_K;
            break;
        case SDLK_l:
            return KI_L;
            break;
        case SDLK_m:
            return KI_M;
            break;
        case SDLK_n:
            return KI_N;
            break;
        case SDLK_o:
            return KI_O;
            break;
        case SDLK_p:
            return KI_P;
            break;
        case SDLK_q:
            return KI_Q;
            break;
        case SDLK_r:
            return KI_R;
            break;
        case SDLK_s:
            return KI_S;
            break;
        case SDLK_t:
            return KI_T;
            break;
        case SDLK_u:
            return KI_U;
            break;
        case SDLK_v:
            return KI_V;
            break;
        case SDLK_w:
            return KI_W;
            break;
        case SDLK_x:
            return KI_X;
            break;
        case SDLK_y:
            return KI_Y;
            break;
        case SDLK_z:
            return KI_Z;
            break;
        case SDLK_SEMICOLON:
            return KI_OEM_1;
            break;
        case SDLK_PLUS:
            return KI_OEM_PLUS;
            break;
        case SDLK_COMMA:
            return KI_OEM_COMMA;
            break;
        case SDLK_MINUS:
            return KI_OEM_MINUS;
            break;
        case SDLK_PERIOD:
            return KI_OEM_PERIOD;
            break;
        case SDLK_SLASH:
            return KI_OEM_2;
            break;
        case SDLK_BACKQUOTE:
            return KI_OEM_3;
            break;
        case SDLK_LEFTBRACKET:
            return KI_OEM_4;
            break;
        case SDLK_BACKSLASH:
            return KI_OEM_5;
            break;
        case SDLK_RIGHTBRACKET:
            return KI_OEM_6;
            break;
        case SDLK_QUOTEDBL:
            return KI_OEM_7;
            break;
        case SDLK_KP_0:
            return KI_NUMPAD0;
            break;
        case SDLK_KP_1:
            return KI_NUMPAD1;
            break;
        case SDLK_KP_2:
            return KI_NUMPAD2;
            break;
        case SDLK_KP_3:
            return KI_NUMPAD3;
            break;
        case SDLK_KP_4:
            return KI_NUMPAD4;
            break;
        case SDLK_KP_5:
            return KI_NUMPAD5;
            break;
        case SDLK_KP_6:
            return KI_NUMPAD6;
            break;
        case SDLK_KP_7:
            return KI_NUMPAD7;
            break;
        case SDLK_KP_8:
            return KI_NUMPAD8;
            break;
        case SDLK_KP_9:
            return KI_NUMPAD9;
            break;
        case SDLK_KP_ENTER:
            return KI_NUMPADENTER;
            break;
        case SDLK_KP_MULTIPLY:
            return KI_MULTIPLY;
            break;
        case SDLK_KP_PLUS:
            return KI_ADD;
            break;
        case SDLK_KP_MINUS:
            return KI_SUBTRACT;
            break;
        case SDLK_KP_PERIOD:
            return KI_DECIMAL;
            break;
        case SDLK_KP_DIVIDE:
            return KI_DIVIDE;
            break;
        case SDLK_KP_EQUALS:
            return KI_OEM_NEC_EQUAL;
            break;
        case SDLK_BACKSPACE:
            return KI_BACK;
            break;
        case SDLK_TAB:
            return KI_TAB;
            break;
        case SDLK_CLEAR:
            return KI_CLEAR;
            break;
        case SDLK_RETURN:
            return KI_RETURN;
            break;
        case SDLK_PAUSE:
            return KI_PAUSE;
            break;
        case SDLK_CAPSLOCK:
            return KI_CAPITAL;
            break;
        case SDLK_PAGEUP:
            return KI_PRIOR;
            break;
        case SDLK_PAGEDOWN:
            return KI_NEXT;
            break;
        case SDLK_END:
            return KI_END;
            break;
        case SDLK_HOME:
            return KI_HOME;
            break;
        case SDLK_LEFT:
            return KI_LEFT;
            break;
        case SDLK_UP:
            return KI_UP;
            break;
        case SDLK_RIGHT:
            return KI_RIGHT;
            break;
        case SDLK_DOWN:
            return KI_DOWN;
            break;
        case SDLK_INSERT:
            return KI_INSERT;
            break;
        case SDLK_DELETE:
            return KI_DELETE;
            break;
        case SDLK_HELP:
            return KI_HELP;
            break;
        case SDLK_F1:
            return KI_F1;
            break;
        case SDLK_F2:
            return KI_F2;
            break;
        case SDLK_F3:
            return KI_F3;
            break;
        case SDLK_F4:
            return KI_F4;
            break;
        case SDLK_F5:
            return KI_F5;
            break;
        case SDLK_F6:
            return KI_F6;
            break;
        case SDLK_F7:
            return KI_F7;
            break;
        case SDLK_F8:
            return KI_F8;
            break;
        case SDLK_F9:
            return KI_F9;
            break;
        case SDLK_F10:
            return KI_F10;
            break;
        case SDLK_F11:
            return KI_F11;
            break;
        case SDLK_F12:
            return KI_F12;
            break;
        case SDLK_F13:
            return KI_F13;
            break;
        case SDLK_F14:
            return KI_F14;
            break;
        case SDLK_F15:
            return KI_F15;
            break;
        case SDLK_NUMLOCKCLEAR:
            return KI_NUMLOCK;
            break;
        case SDLK_SCROLLLOCK:
            return KI_SCROLL;
            break;
        case SDLK_LSHIFT:
            return KI_LSHIFT;
            break;
        case SDLK_RSHIFT:
            return KI_RSHIFT;
            break;
        case SDLK_LCTRL:
            return KI_LCONTROL;
            break;
        case SDLK_RCTRL:
            return KI_RCONTROL;
            break;
        case SDLK_LALT:
            return KI_LMENU;
            break;
        case SDLK_RALT:
            return KI_RMENU;
            break;
        case SDLK_LGUI:
            return KI_LMETA;
            break;
        case SDLK_RGUI:
            return KI_RMETA;
            break;
        /*case SDLK_LSUPER:
            return KI_LWIN;
            break;
        case SDLK_RSUPER:
            return KI_RWIN;
            break;*/
        default:
            return KI_UNKNOWN;
            break;
    }
}


Rocket::Core::Input::KeyModifier RocketConvertSDLmod( Uint16 sdl ) {
	using namespace Rocket::Core::Input;

	int mod = 0;
	if( sdl & KMOD_SHIFT )	mod |= KM_SHIFT;
	if( sdl & KMOD_CTRL )	mod |= KM_CTRL;
	if( sdl & KMOD_ALT )	mod |= KM_ALT;
	if( sdl & KMOD_GUI )	mod |= KM_META;
	if( sdl & KMOD_CAPS )	mod |= KM_CAPSLOCK;
	if( sdl & KMOD_NUM )	mod |= KM_NUMLOCK;

	return KeyModifier( mod );
}


int RocketConvertSDLButton( Uint8 sdlButton ) {
	return sdlButton - 1;
}


PyObject* GetDocumentNamespace(Rocket::Core::ElementDocument * document) {
    Rocket::Core::Python::ElementDocumentWrapper* documentw = dynamic_cast< Rocket::Core::Python::ElementDocumentWrapper* > (document);
	if (!documentw) return NULL;
	PyObject *pynamespace = documentw->GetModuleNamespace();
	Py_INCREF(pynamespace);
	return pynamespace;
}


#if !SDL_RENDER_DISABLED
RocketSDLRenderInterface::RocketSDLRenderInterface(SDL_Renderer *r, SDL_Window *w)
{
    renderer = r;
    window = w;
}

void RocketSDLRenderInterface::Resize()
{
	/*MyWindow->SetActive(true);
	//MyWindow->SaveGLStates();

	static sf::View View;
	//View.SetFromRect(sf::FloatRect(0, (float)MyWindow->GetWidth(), (float)MyWindow->GetHeight(), 0));
	View.SetViewport(sf::FloatRect(0, (float)MyWindow->GetWidth(), (float)MyWindow->GetHeight(), 0));
	MyWindow->SetView(View);

	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0, MyWindow->GetWidth(), MyWindow->GetHeight(), 0, -1, 1);
	glMatrixMode(GL_MODELVIEW);

	glViewport(0, 0, MyWindow->GetWidth(), MyWindow->GetHeight());

	//MyWindow->RestoreGLStates();*/
};



// Called by Rocket when it wants to compile geometry it believes will be static for the forseeable future.
Rocket::Core::CompiledGeometryHandle RocketSDLRenderInterface::CompileGeometry(Rocket::Core::Vertex* ROCKET_UNUSED(vertices), int ROCKET_UNUSED(num_vertices), int* ROCKET_UNUSED(indices), int ROCKET_UNUSED(num_indices), const Rocket::Core::TextureHandle ROCKET_UNUSED(texture))
{
	return (Rocket::Core::CompiledGeometryHandle) NULL;
}

// Called by Rocket when it wants to render application-compiled geometry.
void RocketSDLRenderInterface::RenderCompiledGeometry(Rocket::Core::CompiledGeometryHandle ROCKET_UNUSED(geometry), const Rocket::Core::Vector2f& ROCKET_UNUSED(translation))
{
}

// Called by Rocket when it wants to release application-compiled geometry.
void RocketSDLRenderInterface::ReleaseCompiledGeometry(Rocket::Core::CompiledGeometryHandle ROCKET_UNUSED(geometry))
{
}

// Called by Rocket when a texture is required by the library.
bool RocketSDLRenderInterface::LoadTexture(Rocket::Core::TextureHandle& texture_handle, Rocket::Core::Vector2i& texture_dimensions, const Rocket::Core::String& source)
{
    // TODO: Load this through the Ignifuga's DataManager, probably through a Canvas, it probably requires that we convert DataManager into a Cython class
    // TODO: Support hot reloading if possible...via whole document reloading maybe?
	SDL_Surface *surface = IMG_Load(source.CString());
	if (surface) {
	    SDL_Texture *texture = SDL_CreateTextureFromSurface(renderer, surface);

   	    if (texture) {
   	        texture_handle = (Rocket::Core::TextureHandle) texture;
   	        texture_dimensions = Rocket::Core::Vector2i(surface->w, surface->h);
   	        SDL_FreeSurface(surface);
   	    }
   	    return true;
   	}

   	return false;
}

// Called by Rocket when a texture is required to be built from an internally-generated sequence of pixels.
bool RocketSDLRenderInterface::GenerateTexture(Rocket::Core::TextureHandle& texture_handle, const Rocket::Core::byte* source, const Rocket::Core::Vector2i& source_dimensions)
{
    #if SDL_BYTEORDER == SDL_BIG_ENDIAN
        Uint32 rmask = 0xff000000;
        Uint32 gmask = 0x00ff0000;
        Uint32 bmask = 0x0000ff00;
        Uint32 amask = 0x000000ff;
    #else
        Uint32 rmask = 0x000000ff;
        Uint32 gmask = 0x0000ff00;
        Uint32 bmask = 0x00ff0000;
        Uint32 amask = 0xff000000;
    #endif

    SDL_Surface *surface = SDL_CreateRGBSurfaceFrom ((void*) source, source_dimensions.x, source_dimensions.y, 32, source_dimensions.x*4, rmask, gmask, bmask, amask);
	SDL_Texture *texture = SDL_CreateTextureFromSurface(renderer, surface);
	SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
	SDL_FreeSurface(surface);
	texture_handle = (Rocket::Core::TextureHandle) texture;
	return true;
}

// Called by Rocket when a loaded texture is no longer required.
void RocketSDLRenderInterface::ReleaseTexture(Rocket::Core::TextureHandle texture_handle)
{
	SDL_DestroyTexture((SDL_Texture*) texture_handle);
}

#endif //!SDL_RENDER_DISABLED