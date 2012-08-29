/*
 * Copyright (c) 2010-2012, Gabriel Jacobo
 * All rights reserved.
 * Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
 * whose terms are available in the LICENSE file or at http://www.ignifuga.org/license
 *
 */

#ifndef SDLROCKETGLUEGL_HPP
#define SDLROCKETGLUEGL_HPP

#include "backends/sdl/RocketGlue.hpp"

#if !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL

#if __MINGW32__ || __MINGW64__
#define GL_GLEXT_PROTOTYPES
#endif

#include "SDL_opengl.h"

typedef struct
{
 /* OpenGL functions */
#define SDL_PROC(ret,func,params) ret (APIENTRY *func) params;
#define ROCKET_OPENGL
#include "backends/sdl/RocketGLFuncs.hpp"
#undef SDL_PROC
#undef ROCKET_OPENGL

} RenderDataGL;

class RocketSDLRenderInterfaceOpenGL : public RocketSDLRenderInterface
{
protected:
    RenderDataGL render_data;

public:
	RocketSDLRenderInterfaceOpenGL(SDL_Renderer *r, SDL_Window *w);

	/// Called by Rocket when it wants to render geometry that it does not wish to optimise.
	virtual void RenderGeometry(Rocket::Core::Vertex* vertices, int num_vertices, int* indices, int num_indices, Rocket::Core::TextureHandle texture, const Rocket::Core::Vector2f& translation);
	/// Called by Rocket when it wants to enable or disable scissoring to clip content.
	virtual void EnableScissorRegion(bool enable);
	/// Called by Rocket when it wants to change the scissor region.
	virtual void SetScissorRegion(int x, int y, int width, int height);
};

#endif // !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL

#endif // SDLROCKETGLUEGL_HPP