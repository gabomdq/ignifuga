#ifndef SDLROCKETGLUE_HPP
#define SDLROCKETGLUE_HPP

#include <iostream>
#include "SDL.h"
#include "SDL_config.h"
#include "SDL_image.h"
#include "Python.h"

#include <Rocket/Core/RenderInterface.h>
#include <Rocket/Core/Platform.h>
#include <Rocket/Core.h>
#include <Rocket/Core/SystemInterface.h>
#include <Rocket/Core/FileInterface.h>
#include <Rocket/Controls.h>

Rocket::Core::Context* RocketInit(SDL_Renderer *renderer, SDL_Window *window);
void RocketFree(Rocket::Core::Context *mainCtx);

int SDLKeyToRocketInput(SDL_Keycode sdlkey);
Rocket::Core::Input::KeyModifier RocketConvertSDLmod( Uint16 sdl );
int RocketConvertSDLButton( Uint8 sdlButton );
void InjectRocket( Rocket::Core::Context* context, SDL_Event& event );
PyObject* GetDocumentNamespace(Rocket::Core::ElementDocument *document);

/* Glue for the system interface */
class RocketSDLSystemInterface : public Rocket::Core::SystemInterface
{
	public:
		virtual float GetElapsedTime() {
			return static_cast<float>( SDL_GetTicks() ) / 1000.0f;
		}
};

/* Glue for the file system interface */

class RocketSDLFileInterface : public Rocket::Core::FileInterface {
    public:
	    virtual Rocket::Core::FileHandle Open(const Rocket::Core::String& path) {
	        return (Rocket::Core::FileHandle)SDL_RWFromFile(path.CString(), "r");
	    }

	    virtual void Close(Rocket::Core::FileHandle file) {

	        SDL_RWclose((SDL_RWops*)file);
	    }

    	virtual size_t Read(void* buffer, size_t size, Rocket::Core::FileHandle file) {
            size_t value = SDL_RWread((SDL_RWops*)file, buffer, 1, size);
            return value;
    	}

    	virtual bool Seek(Rocket::Core::FileHandle file, long offset, int origin) {
            SDL_RWseek((SDL_RWops*)file, offset, origin);
            return true;
    	}

    	virtual size_t Tell(Rocket::Core::FileHandle file) {
    	    return SDL_RWtell((SDL_RWops*)file);
    	}
};


class RocketSDLRenderInterface : public Rocket::Core::RenderInterface
{
protected:
    SDL_Renderer *renderer;
    SDL_Window *window;

public:
	RocketSDLRenderInterface(SDL_Renderer *r, SDL_Window *w);

	/// Called by Rocket when it wants to compile geometry it believes will be static for the forseeable future.
	virtual Rocket::Core::CompiledGeometryHandle CompileGeometry(Rocket::Core::Vertex* vertices, int num_vertices, int* indices, int num_indices, Rocket::Core::TextureHandle texture);

	/// Called by Rocket when it wants to render application-compiled geometry.
	virtual void RenderCompiledGeometry(Rocket::Core::CompiledGeometryHandle geometry, const Rocket::Core::Vector2f& translation);
	/// Called by Rocket when it wants to release application-compiled geometry.
	virtual void ReleaseCompiledGeometry(Rocket::Core::CompiledGeometryHandle geometry);

	/// Called by Rocket when a texture is required by the library.
	virtual bool LoadTexture(Rocket::Core::TextureHandle& texture_handle, Rocket::Core::Vector2i& texture_dimensions, const Rocket::Core::String& source);
	/// Called by Rocket when a texture is required to be built from an internally-generated sequence of pixels.
	virtual bool GenerateTexture(Rocket::Core::TextureHandle& texture_handle, const Rocket::Core::byte* source, const Rocket::Core::Vector2i& source_dimensions);
	/// Called by Rocket when a loaded texture is no longer required.
	virtual void ReleaseTexture(Rocket::Core::TextureHandle texture_handle);

	virtual void Resize();
};

#endif // SDLROCKETGLUE_HPP