#!/bin/sh

prog="编译 打包"

#CODE_SIGN_IDENTITY="iPhone Developer: 982380365@qq.com (3937MHCH29)" PROVISIONING_PROFILE=$PROVISIONING_PROFILE_UUID

#基础常量
#证书
CERTIFICATION_NAME='iPhone Developer: 982380365@qq.com (3937MHCH29)'
#描述文件
PROVISIONING_PROFILE_UUID="a6742559-adc2-48c0-9f72-bae327e46aea"
#打包用到的plist文件路径
OptionPlistPath='ipaInfo.plist'
#输出路径
OUTPUT_PATH='output'

prepare () {

# 确认工程是否使用了workspace
# 1: workspace 2: project
TYPE=0

for var in `ls`
do
ext=${var##*.} #扩展名
if [ $ext = "xcworkspace" ]; then
TYPE=1
WORKSPACE=$var
BUILDPATH="build"
break
elif [ $ext = "xcodeproj" ]; then
TYPE=2
PROJECT=$var
fi
done

#获取target和scheme
if [ $TYPE = 1 ]; then
INFO=`xcodebuild -list`
next=0
for var in $INFO
do
if [ $var = "Targets:" ]; then
next=1
elif [ $next = 1 ]; then
TARGET=$var
next=0
elif [ $var = "Schemes:" ]; then
next=2
elif [ $next = 2 ]; then
SCHEME=$var
next=0
fi
done
if [ ! -n "$SCHEME" ]; then
SCHEME=$TARGET
fi
elif [ $TYPE = 2 ]; then
INFO=`xcodebuild -list`
next=0
for var in $INFO
do
if [ $var = "Targets:" ]; then
next=1
elif [ $next = 1 ]; then
TARGET=$var
next=0
elif [ $var = "Schemes:" ]; then
next=2
elif [ $next = 2 ]; then
SCHEME=$var
next=0
fi
done
if [ ! -n "$TARGET" ];then
echo "target not exist"
exit 1
fi
if [ ! -n "$SCHEME" ];then
SCHEME=$TARGET
fi
else
echo "this is not a xcode project"
exit 1
fi
}

#编译项目
build () {
prepare
if [ $TYPE = 1 ]; then
xcodebuild build -workspace $WORKSPACE -scheme $SCHEME -derivedDataPath $BUILDPATH | xcpretty
elif [ $TYPE = 2 ]; then
xcodebuild build -project $PROJECT -target $TARGET | xcpretty
fi
}

#清理项目
clean () {
prepare
if [ $TYPE = 1 ]; then
xcodebuild clean -workspace $WORKSPACE -scheme $SCHEME -derivedDataPath $BUILDPATH | xcpretty
elif [ $TYPE = 2 ]; then
xcodebuild clean -project $PROJECT -target $TARGET | xcpretty
fi
}

#打包项目
archive () {
prepare
if [ ! -f $OptionPlistPath ]; then
#echo "exportOptionsPlist not exist! Please type \"$(basename $0) createPlist\""
createPlist
fi

dateStr=`date +%Y%m%d%H%M%S`

SAVE_PATH="$OUTPUT_PATH/$dateStr"

if [ -e $SAVE_PATH ]; then
rm -rf $SAVE_PATH
fi

ARCHIVE_PATH="$SAVE_PATH/$TARGET.xcarchive"
EXPORT_DIR="$SAVE_PATH/Exported"

if [ $TYPE = 1 ]; then
xcodebuild archive -workspace $WORKSPACE -scheme $SCHEME -configuration Release -archivePath $ARCHIVE_PATH -derivedDataPath $BUILDPATH | xcpretty
elif [ $TYPE = 2 ]; then
xcodebuild archive -project $PROJECT -scheme $SCHEME -configuration Release -archivePath $ARCHIVE_PATH | xcpretty
fi
xcodebuild -exportArchive -archivePath $ARCHIVE_PATH -exportPath $EXPORT_DIR -exportOptionsPlist $OptionPlistPath | xcpretty
open $OUTPUT_PATH

}

#创建exportOptionsPlist文件
createPlist () {
if [ ! -f $OptionPlistPath ]; then
echo '<?xml version="1.0" encoding="UTF-8"?>'\
'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'\
'<plist version="1.0">'\
'<dict>'\
'<key>method</key>'\
'<string>development</string>'\
'<key> compileBitcode</key>'\
'<true/>'\
'</dict>'\
'</plist>' > $OptionPlistPath
echo "create plist success"
fi
}

#脚本入口 根据输入指令选择操作
case "$1" in
"build")
echo "start build"
build;;
"clean")
echo "start clean"
clean;;
"archive")
echo "start archive"
archive;;
"createPlist")
createPlist;;
*)
echo $"Usage: $prog {build|clean|archive|createPlist}";;
#echo 'need install "xcpretty"';;
esac

