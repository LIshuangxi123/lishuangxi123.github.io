// 越狱插件的入口文件示例。
// 真正要改东西的时候，把下面 %hook 那段取消注释，改成你想 hook 的类和方法。
// 改完在项目目录执行 make package 就能打出 deb。

#import <Foundation/Foundation.h>

%ctor {
    NSLog(@"[HelloTweak] 插件已加载");
}

/*
%hook SBHomeScreenViewController

- (void)viewDidLoad {
    %orig;
    // 这里写你的逻辑
}

%end
*/
