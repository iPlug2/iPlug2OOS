
#include <TargetConditionals.h>
#if TARGET_OS_IOS == 1
#import <UIKit/UIKit.h>
#else
#import <Cocoa/Cocoa.h>
#endif

#define IPLUG_AUVIEWCONTROLLER IPlugAUViewController_vVisageTemplate
#define IPLUG_AUAUDIOUNIT IPlugAUAudioUnit_vVisageTemplate
#import <VisageTemplateAU/IPlugAUViewController.h>
#import <VisageTemplateAU/IPlugAUAudioUnit.h>

//! Project version number for VisageTemplateAU.
FOUNDATION_EXPORT double VisageTemplateAUVersionNumber;

//! Project version string for VisageTemplateAU.
FOUNDATION_EXPORT const unsigned char VisageTemplateAUVersionString[];

@class IPlugAUViewController_vVisageTemplate;
