
#include <TargetConditionals.h>
#if TARGET_OS_IOS == 1 || TARGET_OS_VISION == 1
#import <UIKit/UIKit.h>
#else
#import <Cocoa/Cocoa.h>
#endif

#define IPLUG_AUVIEWCONTROLLER IPlugAUViewController_vTemplateProjectWebView
#define IPLUG_AUAUDIOUNIT IPlugAUAudioUnit_vTemplateProjectWebView
#import <TemplateProjectWebViewAU/IPlugAUViewController.h>
#import <TemplateProjectWebViewAU/IPlugAUAudioUnit.h>

//! Project version number for TemplateProjectWebViewAU.
FOUNDATION_EXPORT double TemplateProjectWebViewAUVersionNumber;

//! Project version string for TemplateProjectWebViewAU.
FOUNDATION_EXPORT const unsigned char TemplateProjectWebViewAUVersionString[];

@class IPlugAUViewController_vTemplateProjectWebView;
