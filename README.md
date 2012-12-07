About the [Ignifuga Game Engine](http://ignifuga.org)
==============================

Ignifuga is a multi platform (Windows/Linux/OS X/iOS/Android) 2D hardware accelerated engine based on Python and Cython,
inspired by similar offerings like Cocos2D, Cocos2D for iPhone, and AndEngine. All your game logic code along with the
engine’s and supporting tools is converted to C during the build process, and compiled into one big standalone binary
for each of the supported platforms (please refer to the FAQ for more information). The project is currently in heavy
development as the engine for [The Gaucho](http://whoisthegaucho.com), and it should be fairly usable already, but we don’t give any guarantees, so
the expected performance may range from not even working to attaining consciousness and starting the third world war for
all we know. At the very least, we hope that it lives up to its name and it doesn’t catch fire.

Features
========

* 2D game engine
* Python/Cython based – compiles all the code to a static binary, no external dependencies.
* Targets:
    * Linux 32 and 64 bits
    * Windows 32 (64 bits support almost done)
    * OS X (10.6 and newer, i386 and x86_64)
    * Android (ARM CPUs, version 2.0 and newer)
    * All iOS devices from the original iPhone to the new iPad 3 and iPhone 5 (iOS 3.0 and newer, including 6.x, with the iOS SDK v5.0 or newer, armv6, armv7 and armv7s devices)
    * More coming soon…
* Component based design, add your own components, use or extend the default set:
    * Actions (dynamic modification of any of the entity components and properties)
    * Sprites: static and animated, hardware accelerated, automatically compressed (see the Grossman tool for details). Fast and automatic scaling, red/green/blue/alpha modification, bluring,etc.
    * Text (with TTF font support)
    * Sound (with ogg support)
    * Music (with ogg support)
* libRocket integration, build your GUI using HTML+CSS!
* Remote Python Console via RFoo integration, connect remotely to a running instance of Ignifuga and experiment with your game interactively in real time.
* pQuery, our own version of jQuery for Python, that works on Ignifuga Scenes/Entities/Components and Rocket RML Elements using the exact same syntax.
* Despite compiling everything to C and then to machine code, you can still take advantage of Python’s dynamic nature and develop using almost regular Python in your dev system, then compile everything into a neat bundle for distribution
* Heavily data driven, almost everything can be done from a json definition file
* Hot (on the fly, pun intended) reloading of assets, this includes images and scene definition files.
* The Schafer tool, which automates the whole build process for all the supported platforms
* Schafer’s “bare” mode, which builds a custom static Python interpreter with the minimum possible contents (no SDL, no libRocket, etc) plus your source code, on all the supported platforms, very useful for easy distribution of Python based projects entirely unrelated to games or chickens!
* The Grossman tool, which processes sets of sprites into a monolithic compressed texture, generating no hassle animated sprites with optimized hit maps with transparency support

Why Ignifuga? Who is he/her/it? What's in a name?
=================================================

Ignifuga means fireproof in spanish. That doesn’t explain much, and it has little to do with game engines, I know.
But it’s a catchy name, I already had the art from a dead-and-now-revived project,
and the Linux project has a penguin in their logo, so don’t come here judging me!

Where should I begin?
=====================

[Check out our Getting Started guide](http://ignifuga.org/gettingstarted)

The demo project is outdated and it doesn't make justice to the newer features, but it should do in the meantime,
so [check it out](https://bitbucket.org/gabomdq/ignifuga-demo) (in the meantime to what you ask? Good question!)


