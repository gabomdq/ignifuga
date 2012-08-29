/*
 * Copyright (c) 2010-2012, Gabriel Jacobo
 * All rights reserved.
 * Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
 * whose terms are available in the LICENSE file or at http://www.ignifuga.org/license
 *
 */

#ifndef SDLROCKETGLUEGLES_HPP
#define SDLROCKETGLUEGLES_HPP

#include "backends/sdl/RocketGlue.hpp"

#if !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES
#include "SDL_opengles.h"

typedef struct
{
 /* OpenGL functions */
#define SDL_PROC(ret,func,params) ret (APIENTRY *func) params;
#define ROCKET_OPENGLES
#include "backends/sdl/RocketGLFuncs.hpp"
#undef SDL_PROC
#undef ROCKET_OPENGLES

} RenderDataGLES;

class RocketSDLRenderInterfaceOpenGLES : public RocketSDLRenderInterface
{
protected:
    RenderDataGLES render_data;

public:
	RocketSDLRenderInterfaceOpenGLES(SDL_Renderer *r, SDL_Window *w);

	/// Called by Rocket when it wants to render geometry that it does not wish to optimise.
	virtual void RenderGeometry(Rocket::Core::Vertex* vertices, int num_vertices, int* indices, int num_indices, Rocket::Core::TextureHandle texture, const Rocket::Core::Vector2f& translation);
	/// Called by Rocket when it wants to enable or disable scissoring to clip content.
	virtual void EnableScissorRegion(bool enable);
	/// Called by Rocket when it wants to change the scissor region.
	virtual void SetScissorRegion(int x, int y, int width, int height);
};

#endif // !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES

#endif // SDLROCKETGLUEGLES_HPP