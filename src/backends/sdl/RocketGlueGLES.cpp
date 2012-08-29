/*
 * Copyright (c) 2010-2012, Gabriel Jacobo
 * All rights reserved.
 * Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
 * whose terms are available in the LICENSE file or at http://www.ignifuga.org/license
 *
 */

#include "backends/sdl/RocketGlueGLES.hpp"

#if defined(ANDROID)
#include <android/log.h>
#endif

#if !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES
RocketSDLRenderInterfaceOpenGLES::RocketSDLRenderInterfaceOpenGLES(SDL_Renderer *r, SDL_Window *w) : RocketSDLRenderInterface(r,w)
{
    #define SDL_PROC SDL_PROC_CPP
    #define ROCKET_OPENGLES
    #include "backends/sdl/RocketGLFuncs.hpp"
    #undef SDL_PROC
    #undef ROCKET_OPENGLES
}

// Called by Rocket when it wants to render geometry that it does not wish to optimise.
void RocketSDLRenderInterfaceOpenGLES::RenderGeometry(Rocket::Core::Vertex* vertices, int num_vertices, int* indices, int num_indices, const Rocket::Core::TextureHandle texture, const Rocket::Core::Vector2f& translation)
{
    render_data.glPushMatrix();
	render_data.glTranslatef(translation.x, translation.y, 0);

	std::vector<Rocket::Core::Vector2f> Positions(num_vertices);
	std::vector<Rocket::Core::Colourb> Colors(num_vertices);
	std::vector<Rocket::Core::Vector2f> TexCoords(num_vertices);
	float texw, texh;

    SDL_Texture* sdl_texture = NULL;
    if(texture)
    {
        render_data.glEnableClientState(GL_TEXTURE_COORD_ARRAY);
        sdl_texture = (SDL_Texture *) texture;
        SDL_GL_BindTexture(sdl_texture, &texw, &texh);
    }

	for(int  i = 0; i < num_vertices; i++)
	{
		Positions[i] = vertices[i].position;
		Colors[i] = vertices[i].colour;
		if (sdl_texture) {
		    TexCoords[i].x = vertices[i].tex_coord.x * texw;
		    TexCoords[i].y = vertices[i].tex_coord.y * texh;
		}
		else TexCoords[i] = vertices[i].tex_coord;
	};

	unsigned short newIndicies[num_indices];
    for (int i = 0; i < num_indices; i++)
    {
      newIndicies[i] = (unsigned short) indices[i];
    }

	render_data.glEnableClientState(GL_VERTEX_ARRAY);
	render_data.glEnableClientState(GL_COLOR_ARRAY);
	render_data.glVertexPointer(2, GL_FLOAT, 0, &Positions[0]);
	render_data.glColorPointer(4, GL_UNSIGNED_BYTE, 0, &Colors[0]);
	render_data.glTexCoordPointer(2, GL_FLOAT, 0, &TexCoords[0]);

	render_data.glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
	render_data.glEnable(GL_BLEND);
	render_data.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	render_data.glDrawElements(GL_TRIANGLES, num_indices, GL_UNSIGNED_SHORT, newIndicies);
	render_data.glDisableClientState(GL_VERTEX_ARRAY);
	render_data.glDisableClientState(GL_COLOR_ARRAY);
	render_data.glDisableClientState(GL_TEXTURE_COORD_ARRAY);

	if (sdl_texture) {
        SDL_GL_UnbindTexture(sdl_texture);
    	render_data.glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    }

	render_data.glColor4f(1.0, 1.0, 1.0, 1.0);

	render_data.glPopMatrix();
}
// Called by Rocket when it wants to enable or disable scissoring to clip content.
void RocketSDLRenderInterfaceOpenGLES::EnableScissorRegion(bool enable)
{
	if (enable)
		render_data.glEnable(GL_SCISSOR_TEST);
	else
		render_data.glDisable(GL_SCISSOR_TEST);
}

// Called by Rocket when it wants to change the scissor region.
void RocketSDLRenderInterfaceOpenGLES::SetScissorRegion(int x, int y, int width, int height)
{
	int w_width, w_height;
	SDL_GetWindowSize(window, &w_width, &w_height);
	render_data.glScissor(x, w_height - (y + height), width, height);
}

#endif // !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES