#ifndef SDLROCKETGLUEGLES2_HPP
#define SDLROCKETGLUEGLES2_HPP

#include "backends/sdl/RocketGlue.hpp"
#include <string>

#if !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES2
#include "SDL_opengles2.h"

typedef struct
{
 /* OpenGL functions */
#define SDL_PROC(ret,func,params) ret (APIENTRY *func) params;
#define ROCKET_OPENGLES2
#include "backends/sdl/RocketGLFuncs.hpp"
#undef SDL_PROC
#undef ROCKET_OPENGLES2

} RenderDataGLES2;

class RocketSDLRenderInterfaceOpenGLES2 : public RocketSDLRenderInterface
{
private:
    //std::string RocketGlueFragmentShader, RocketGlueVertexShader;

protected:
    RenderDataGLES2 render_data;
    GLuint program_texture_id, program_color_id, fragment_texture_shader_id, fragment_color_shader_id, vertex_shader_id;
    GLuint u_texture, u_texture_projection, u_texture_translation, u_color_projection, u_color_translation;

public:
	RocketSDLRenderInterfaceOpenGLES2(SDL_Renderer *r, SDL_Window *w);

	/// Called by Rocket when it wants to render geometry that it does not wish to optimise.
	virtual void RenderGeometry(Rocket::Core::Vertex* vertices, int num_vertices, int* indices, int num_indices, Rocket::Core::TextureHandle texture, const Rocket::Core::Vector2f& translation);
	/// Called by Rocket when it wants to enable or disable scissoring to clip content.
	virtual void EnableScissorRegion(bool enable);
	/// Called by Rocket when it wants to change the scissor region.
	virtual void SetScissorRegion(int x, int y, int width, int height);
};

#endif // !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES2

#endif // SDLROCKETGLUEGLES2_HPP