#include "backends/sdl/RocketGlueGLES2.hpp"

#if defined(ANDROID)
#include <android/log.h>
#endif

#if !SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES2

typedef enum {
    ROCKETGLUE_ATTRIBUTE_POSITION = 0,
    ROCKETGLUE_ATTRIBUTE_TEXCOORD = 1,
    ROCKETGLUE_ATTRIBUTE_COLOR = 2
} ROCKETGLUE_ATTRIBUTES;

typedef enum
{
    ROCKETGLUE_UNIFORM_PROJECTION = 0,
    ROCKETGLUE_UNIFORM_TEXTURE = 1,
    ROCKETGLUE_UNIFORM_TRANSLATION = 0,
} ROCKETGLUE_UNIFORM;

static const char RocketGlueFragmentTextureShader[] = " \
    precision mediump float; \
    varying vec2 v_texCoord; \
    varying vec4 v_color; \
    uniform sampler2D u_texture; \
\
    void main() \
    { \
        gl_FragColor = texture2D( u_texture, v_texCoord ) * v_color; \
    } \
";

static const char RocketGlueFragmentColorShader[] = " \
    precision mediump float; \
    varying vec2 v_texCoord; \
    varying vec4 v_color; \
\
    void main() \
    { \
        gl_FragColor = v_color; \
    } \
";

static const char RocketGlueVertexShader[] = " \
    attribute vec2 a_position; \
    attribute vec2 a_texCoord; \
    attribute vec4 a_color; \
    varying vec2 v_texCoord; \
    varying vec4 v_color; \
    varying vec2 v_position; \
    uniform mat4 u_projection; \
    uniform vec2 u_translation; \
\
    void main() \
    { \
        v_position = a_position + u_translation; \
        gl_Position = u_projection * vec4(v_position, 0.0, 1.0); \
        v_texCoord = a_texCoord; \
        v_color = a_color; \
    }\
";



RocketSDLRenderInterfaceOpenGLES2::RocketSDLRenderInterfaceOpenGLES2(SDL_Renderer *r, SDL_Window *w) : RocketSDLRenderInterface(r,w)
{
    #define SDL_PROC SDL_PROC_CPP
    #define ROCKET_OPENGLES2
    #include "backends/sdl/RocketGLFuncs.hpp"
    #undef SDL_PROC
    #undef ROCKET_OPENGLES2

    render_data.glGetError();
    // We call SDL_RenderClear to make sure the GL context is properly set up
    SDL_RenderClear(r);

    /* Create shaders */
    GLint compileSuccessful = GL_FALSE, linkSuccessful = GL_FALSE;
    GLenum glerr;

    /* Textured fragment shader */
    fragment_texture_shader_id = render_data.glCreateShader(GL_FRAGMENT_SHADER);
    const char* fragment_texture_source[1] = {RocketGlueFragmentTextureShader};
    const GLint fragment_texture_len[1] = {(GLint)sizeof(RocketGlueFragmentTextureShader)-1};
    render_data.glShaderSource(fragment_texture_shader_id, 1, fragment_texture_source, fragment_texture_len);
    render_data.glCompileShader(fragment_texture_shader_id);
    render_data.glGetShaderiv(fragment_texture_shader_id, GL_COMPILE_STATUS, &compileSuccessful);

    glerr = render_data.glGetError();
    if( glerr != GL_NO_ERROR || ! compileSuccessful) {
        char errorLog[4096];
        int length;
        render_data.glGetShaderInfoLog(	fragment_texture_shader_id, 4096, &length, errorLog);
        #if defined(ANDROID)
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "RocketGlue: Failed to compile fragment shader: %u %s", glerr, errorLog);
        #else
        printf("RocketGlue: Failed to compile fragment shader %u %s\n", glerr, errorLog);
        fflush(stdout);
        #endif
        exit(1);
        return;
    }

    /* Colored fragment shader */
    compileSuccessful = GL_FALSE;
    fragment_color_shader_id = render_data.glCreateShader(GL_FRAGMENT_SHADER);
    const char* fragment_color_source[1] = {RocketGlueFragmentColorShader};
    const GLint fragment_color_len[1] = {(GLint)sizeof(RocketGlueFragmentColorShader)-1};
    render_data.glShaderSource(fragment_color_shader_id, 1, fragment_color_source, fragment_color_len);
    render_data.glCompileShader(fragment_color_shader_id);
    render_data.glGetShaderiv(fragment_color_shader_id, GL_COMPILE_STATUS, &compileSuccessful);

    glerr = render_data.glGetError();
    if( glerr != GL_NO_ERROR || ! compileSuccessful) {
        char errorLog[4096];
        int length;
        render_data.glGetShaderInfoLog(	fragment_color_shader_id, 4096, &length, errorLog);
        #if defined(ANDROID)
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "RocketGlue: Failed to compile fragment shader: %u %s", glerr, errorLog);
        #else
        printf("RocketGlue: Failed to compile fragment shader %u %s\n", glerr, errorLog);
        fflush(stdout);
        #endif
        exit(1);
        return;
    }

    compileSuccessful = GL_FALSE;
    vertex_shader_id = render_data.glCreateShader(GL_VERTEX_SHADER);
    const char* vertex_source[1] = {RocketGlueVertexShader};
    const GLint vertex_len[1] = {(GLint)sizeof(RocketGlueVertexShader)-1};
    render_data.glShaderSource(vertex_shader_id, 1, vertex_source, vertex_len);
    render_data.glCompileShader(vertex_shader_id);
    render_data.glGetShaderiv(vertex_shader_id, GL_COMPILE_STATUS, &compileSuccessful);

    glerr = render_data.glGetError();
    if( glerr != GL_NO_ERROR || ! compileSuccessful) {
        char errorLog[4096];
        int length;
        render_data.glGetShaderInfoLog(	vertex_shader_id, 4096, &length, errorLog);
        #if defined(ANDROID)
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "RocketGlue: Failed to compile vertex shader: %u %s", glerr, errorLog);
        #else
        printf("RocketGlue: Failed to compile vertex shader %u %s\n", glerr, errorLog);
        fflush(stdout);
        #endif
        exit(1);
        return;
    }

    /* Create Programs */

    program_texture_id = render_data.glCreateProgram();
    render_data.glAttachShader(program_texture_id, vertex_shader_id);
    render_data.glAttachShader(program_texture_id, fragment_texture_shader_id);
    render_data.glBindAttribLocation(program_texture_id, ROCKETGLUE_ATTRIBUTE_POSITION, "a_position");
    render_data.glBindAttribLocation(program_texture_id, ROCKETGLUE_ATTRIBUTE_TEXCOORD, "a_texCoord");
    render_data.glBindAttribLocation(program_texture_id, ROCKETGLUE_ATTRIBUTE_COLOR, "a_color");
    render_data.glLinkProgram(program_texture_id);
    render_data.glGetProgramiv(program_texture_id, GL_LINK_STATUS, &linkSuccessful);

    glerr = render_data.glGetError();
    if ( glerr != GL_NO_ERROR || !linkSuccessful)
    {
        char errorLog[4096] = "";
        int length;
        render_data.glGetProgramInfoLog( program_texture_id, 4096, &length, errorLog);
        #if defined(ANDROID)
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "RocketGlue: Failed to link GLES2 program: %u %s", glerr, errorLog);
        #else
        printf("RocketGlue: Failed to link GLES2 program: %u %s\n", glerr, errorLog);
        fflush(stdout);
        #endif
        exit(1);
        return;
    }

    u_texture = render_data.glGetUniformLocation(program_texture_id, "u_texture");
    u_texture_projection = render_data.glGetUniformLocation(program_texture_id, "u_projection");
    u_texture_translation = render_data.glGetUniformLocation(program_texture_id, "u_translation");

    program_color_id = render_data.glCreateProgram();
    render_data.glAttachShader(program_color_id, vertex_shader_id);
    render_data.glAttachShader(program_color_id, fragment_color_shader_id);
    render_data.glBindAttribLocation(program_color_id, ROCKETGLUE_ATTRIBUTE_POSITION, "a_position");
    render_data.glBindAttribLocation(program_color_id, ROCKETGLUE_ATTRIBUTE_TEXCOORD, "a_texCoord");
    render_data.glBindAttribLocation(program_color_id, ROCKETGLUE_ATTRIBUTE_COLOR, "a_color");
    render_data.glLinkProgram(program_color_id);
    render_data.glGetProgramiv(program_color_id, GL_LINK_STATUS, &linkSuccessful);

    glerr = render_data.glGetError();
    if ( glerr != GL_NO_ERROR || !linkSuccessful)
    {
        char errorLog[4096] = "";
        int length;
        render_data.glGetProgramInfoLog( program_color_id, 4096, &length, errorLog);
        #if defined(ANDROID)
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "RocketGlue: Failed to link GLES2 program: %u %s", glerr, errorLog);
        #else
        printf("RocketGlue: Failed to link GLES2 program: %u %s\n", glerr, errorLog);
        fflush(stdout);
        #endif
        exit(1);
        return;
    }

    u_color_projection = render_data.glGetUniformLocation(program_color_id, "u_projection");
    u_color_translation = render_data.glGetUniformLocation(program_color_id, "u_translation");

    #if defined(ANDROID)
    __android_log_print(ANDROID_LOG_DEBUG, "SDL", "RocketGlueGLES2 initialized");
    #else
    printf("RocketGlueGLES2 initialized\n");
    fflush(stdout);
    #endif
}

// Called by Rocket when it wants to render geometry that it does not wish to optimise.
void RocketSDLRenderInterfaceOpenGLES2::RenderGeometry(Rocket::Core::Vertex* vertices, int num_vertices, int* indices, int num_indices, const Rocket::Core::TextureHandle texture, const Rocket::Core::Vector2f& translation)
{
    SDL_Texture* sdl_texture = NULL;
    if(texture) render_data.glUseProgram(program_texture_id);
    else render_data.glUseProgram(program_color_id);
    int width, height;
    SDL_Rect rvp;
    SDL_RenderGetViewport(renderer, &rvp);

    GLfloat projection[4][4];

    // Prepare an orthographic projection
    projection[0][0] = 2.0f / rvp.w;
    projection[0][1] = 0.0f;
    projection[0][2] = 0.0f;
    projection[0][3] = 0.0f;
    projection[1][0] = 0.0f;
    //if (renderer->target) {
    //    projection[1][1] = 2.0f / height;
    //} else {
        projection[1][1] = -2.0f / rvp.h;
    //}
    projection[1][2] = 0.0f;
    projection[1][3] = 0.0f;
    projection[2][0] = 0.0f;
    projection[2][1] = 0.0f;
    projection[2][2] = 0.0f;
    projection[2][3] = 0.0f;
    projection[3][0] = -1.0f;
    //if (renderer->target) {
    //    projection[3][1] = -1.0f;
    //} else {
        projection[3][1] = 1.0f;
    //}
    projection[3][2] = 0.0f;
    projection[3][3] = 1.0f;

    // Set the projection matrix
    if (texture) {
        render_data.glUniformMatrix4fv(u_texture_projection, 1, GL_FALSE, (GLfloat *)projection);
        render_data.glUniform2f(u_texture_translation, translation.x, translation.y);
    }
    else {
        render_data.glUniformMatrix4fv(u_color_projection, 1, GL_FALSE, (GLfloat *)projection);
        render_data.glUniform2f(u_color_translation, translation.x, translation.y);
    }

    render_data.glEnable(GL_BLEND);
    render_data.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    float texw, texh;

    unsigned short newIndicies[num_indices];
    for (int i = 0; i < num_indices; i++)
    {
      newIndicies[i] = (unsigned short) indices[i];
    }

    glVertexAttribPointer(ROCKETGLUE_ATTRIBUTE_POSITION, 2, GL_FLOAT, GL_FALSE, sizeof(Rocket::Core::Vertex), &vertices[0].position);
    glVertexAttribPointer(ROCKETGLUE_ATTRIBUTE_COLOR, 4, GL_UNSIGNED_BYTE, GL_TRUE, sizeof(Rocket::Core::Vertex), &vertices[0].colour);
    render_data.glEnableVertexAttribArray(ROCKETGLUE_ATTRIBUTE_POSITION);
    render_data.glEnableVertexAttribArray(ROCKETGLUE_ATTRIBUTE_TEXCOORD);
    render_data.glEnableVertexAttribArray(ROCKETGLUE_ATTRIBUTE_COLOR);

    if(texture) {
        sdl_texture = (SDL_Texture *) texture;
        SDL_GL_BindTexture(sdl_texture, &texw, &texh);
        render_data.glUniform1i(u_texture, 0);
        glVertexAttribPointer(ROCKETGLUE_ATTRIBUTE_TEXCOORD, 2, GL_FLOAT, GL_FALSE, sizeof(Rocket::Core::Vertex), &vertices[0].tex_coord);
    }
    else {
        render_data.glActiveTexture(GL_TEXTURE0);
        render_data.glDisable(GL_TEXTURE_2D);
        render_data.glDisableVertexAttribArray(ROCKETGLUE_ATTRIBUTE_TEXCOORD);
    }

    render_data.glDrawElements(GL_TRIANGLES, num_indices, GL_UNSIGNED_SHORT, newIndicies);

    /* We can disable ROCKETGLUE_ATTRIBUTE_COLOR (2) safely as SDL will reenable the vertex attrib 2 if it is required */
    render_data.glDisableVertexAttribArray(ROCKETGLUE_ATTRIBUTE_COLOR);

    /* Leave ROCKETGLUE_ATTRIBUTE_POSITION (0) and ROCKETGLUE_ATTRIBUTE_TEXCOORD (1) enabled for compatibility with SDL which
       doesn't re enable them when you call RenderCopy/Ex */
    if(sdl_texture) SDL_GL_UnbindTexture(sdl_texture);
    else render_data.glEnableVertexAttribArray(ROCKETGLUE_ATTRIBUTE_TEXCOORD);

    /* Reset blending and draw a fake point just outside the screen to let SDL know that it needs to reset its state in case it wants to render a texture */
    render_data.glDisable(GL_BLEND);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
    SDL_RenderDrawPoint(renderer, -1, -1);

}
// Called by Rocket when it wants to enable or disable scissoring to clip content.
void RocketSDLRenderInterfaceOpenGLES2::EnableScissorRegion(bool enable)
{
	if (enable)
		render_data.glEnable(GL_SCISSOR_TEST);
	else
		render_data.glDisable(GL_SCISSOR_TEST);
}

// Called by Rocket when it wants to change the scissor region.
void RocketSDLRenderInterfaceOpenGLES2::SetScissorRegion(int x, int y, int width, int height)
{
	int w_width, w_height;
	SDL_GetWindowSize(window, &w_width, &w_height);
	render_data.glScissor(x, w_height - (y + height), width, height);
}

#endif //!SDL_RENDER_DISABLED && SDL_VIDEO_RENDER_OGL_ES2