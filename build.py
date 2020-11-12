#!/usr/bin/env python3

import subprocess
import json
import plistlib
import os
import re
import sys
import argparse

class CommandError(Exception):
  pass

class SchemeError(Exception):
  pass

class ExportOptionError(Exception):
  pass

class ExportTypeError(Exception):
  pass

class SignError(Exception):
  pass

class BuildCommand(object):

  BUILD="build"
  CLEAN="clean"
  ARCHIVE="archive"
  EXPORTARCHIVE="exportArchive"

  def __init__(self, command, targetName = None, projectName = None, workspaceName = None, scheme = None, configuration = 'Release', bundleIdentifier = None, certificationName = None, provisionProfileName = None, teamId = None, exportType = 'ad-hoc', archivePath = './output/app.xcarchive', exportPath = './output/app/', exportOptionsPath = './output/ExportOptions.plist', derivedDataPath = './build/', uploadSymbols = True):
    self.command = command

    self.targetName = targetName
    self.projectName = projectName
    self.workspaceName = workspaceName
    self.scheme = scheme
    self.configuration = configuration
    self.bundleIdentifier = bundleIdentifier
    self.certificationName = certificationName
    self.provisionProfileName = provisionProfileName
    self.teamId = teamId
    
    self.exportType = exportType
    self.archivePath = archivePath
    self.exportPath = exportPath
    self.exportOptionsPath = exportOptionsPath

    self.derivedDataPath = derivedDataPath

    self.compileBitcode = True
    self.signingStyle = None
    self.stripSwiftSymbols = True
    self.uploadSymbols = uploadSymbols

    self._otherArgs = []

  @property
  def otherArgs(self):
    return self._otherArgs

  @otherArgs.setter
  def otherArgs(self, value):
    self._otherArgs = value

  def buildCommand(self):
    cmd = ['xcodebuild']

    if self.command == 'build' or self.command == 'archive' or self.command == 'clean':
      cmd.extend([self.command])
      if self.workspaceName and len(self.workspaceName) > 0:
        #use workspaceName
        cmd.extend(['-workspace', self.workspaceName])
      elif self.projectName and len(self.projectName) > 0:
        cmd.extend(['-project', self.projectName])
      else:
        raise SchemeError("workspace or project is empty!")

      if self.scheme and len(self.scheme) > 0:
        cmd.extend(['-scheme', self.scheme])
      else:
        raise SchemeError("Scheme is empty!")
      
      if self.configuration and len(self.configuration) > 0:
        cmd.extend(['-configuration', self.configuration])

      if self.derivedDataPath and len(self.derivedDataPath) > 0:
        cmd.extend(['-derivedDataPath', self.derivedDataPath])

      if self.command == 'build' or self.command == 'archive':
        if self.command == 'archive':
          if self.archivePath and len(self.archivePath) > 0:
            cmd.extend(['-archivePath', self.archivePath])
            pass

        if self.certificationName and len(self.certificationName) > 0:
          cmd.append('CODE_SIGN_IDENTITY=' + self.certificationName)
        if self.provisionProfileName and len(self.provisionProfileName) > 0:
          cmd.append('PROVISIONING_PROFILE_SPECIFIER=' + self.provisionProfileName)
        if self.teamId and len(self.teamId) > 0:
          cmd.append('DEVELOPMENT_TEAM=' + self.teamId)
        if self.bundleIdentifier and len(self.bundleIdentifier) > 0:
          cmd.append('PRODUCT_BUNDLE_IDENTIFIER=' + self.bundleIdentifier)

    else:
      cmd.append('-exportArchive')
      if self.archivePath and len(self.archivePath) > 0:
        cmd.extend(['-archivePath', self.archivePath])

      if self.exportPath and len(self.exportPath) > 0:
        cmd.extend(['-exportPath', self.exportPath])

      if self.exportOptionsPath and len(self.exportOptionsPath) > 0:
        cmd.extend(['-exportOptionsPlist', self.exportOptionsPath])
      pass
    if isinstance(self._otherArgs, list) and len(self._otherArgs) > 0:
      cmd.extend(self._otherArgs)
    return cmd


  def createOptionPlistFile(self):
    if self.exportOptionsPath == None or len(self.exportOptionsPath) == 0:
      raise ExportOptionError("Export options file empty!")
    
    if self.exportType not in ['ad-hoc', 'development', 'app-store', 'enterprise']:
      raise ExportTypeError('Export type error!')

    info = {}
    info['method'] = self.exportType
    info['destination'] = 'export'
    info['compileBitcode'] = self.compileBitcode

    # check again
    if self.signingStyle == 'Manual':
      if self.certificationName == None or len(self.certificationName) == 0:
        raise SignError('certificationName error!')
      if self.provisionProfileName == None or len(self.provisionProfileName) == 0:
        raise SignError('certificationName error!')
      if self.teamId == None or len(self.teamId) == 0:
        raise SignError('certificationName error!')
      if self.bundleIdentifier == None or len(self.bundleIdentifier) == 0:
        raise SignError('certificationName error!')

    # TODO: multiple project settings
    info['provisioningProfiles'] = {
      self.bundleIdentifier: self.provisionProfileName
    }
    info['signingCertificate'] = self.certificationName
    info['signingStyle'] = self.signingStyle
    info['stripSwiftSymbols'] = self.stripSwiftSymbols
    info['teamID'] = self.teamId
    if self.exportType == 'ad-hoc' or self.exportType == 'development':
      info['thinning'] = '<none>'
    elif mode == 'app-store':
      info['uploadSymbols'] = self.uploadSymbols

    dirForOptionPath = os.path.split(self.exportOptionsPath)[0]
    if os.path.isdir(dirForOptionPath) == False:
      os.makedirs(dirForOptionPath)

    with open(self.exportOptionsPath, 'wb') as file:
      plistlib.dump(info, file)

  
  def loadProjectSettings(self): 
    if self.configuration == None or len(self.configuration) == 0:
      self.configuration = "Debug"
    result = self.runCommandWithCallback(['xcodebuild', '-showBuildSettings', '-configuration', self.configuration]).decode('utf-8')
    reg = re.compile(r'CODE_SIGN_STYLE\s+=\s+([\w\W]+?)\n')
    self.signingStyle = reg.search(result).group(1)

    if self.signingStyle == 'Manual':
      if self.certificationName == None or len(self.certificationName) == 0:
        reg = re.compile(r'CODE_SIGN_IDENTITY\s+=\s+([\w\W]+?)\n')
        self.certificationName = reg.search(result).group(1)
      
      if self.provisionProfileName == None or len(self.provisionProfileName) == 0:
        reg = re.compile(r'PROVISIONING_PROFILE_SPECIFIER\s+=\s+([\w\W]+?)\n')
        self.provisionProfileName = reg.search(result).group(1)

      if self.teamId == None or len(self.teamId) == 0:
        reg = re.compile(r'DEVELOPMENT_TEAM\s+=\s+([\w\W]+?)\n')
        self.teamId = reg.search(result).group(1)

      if self.bundleIdentifier == None or len(self.bundleIdentifier) == 0:
        reg = re.compile(r'PRODUCT_BUNDLE_IDENTIFIER\s+=\s+([\w\W]+?)\n')
        self.bundleIdentifier = reg.search(result).group(1)

      reg = re.compile(r'ENABLE_BITCODE\s+=\s+([\w\W]+?)\n')
      self.compileBitcode = reg.search(result).group(1) == 'YES'

      reg = re.compile(r'STRIP_SWIFT_SYMBOLS\s+=\s+([\w\W]+?)\n')
      self.stripSwiftSymbols = reg.search(result).group(1) == 'YES'

  def runCommandWithCallback(self, args):
    return subprocess.check_output(args)

  def runCommand(self, args):
    p = subprocess.Popen(args)
    return p.wait()

  def run(self):
    if self.command not in [self.BUILD, self.CLEAN, self.ARCHIVE, self.EXPORTARCHIVE]:
      raise CommandError("Invalid build command!")
    self.loadProjectSettings()
    if self.command == 'exportArchive':
      self.createOptionPlistFile()
    
    cmd = self.buildCommand()
    return self.runCommand(cmd)
    

def parseArguments():
  parser = argparse.ArgumentParser(description="help")
  parser.add_argument('--project', '-p', help="project name for project")
  parser.add_argument('--target', '-t', help="target name for project")
  parser.add_argument('--workspace', '-w', help="workspace for project")
  parser.add_argument('--scheme', '-s', help="scheme for project")
  parser.add_argument('--configuration', '-c', help="configuration for project", default="Release")
  parser.add_argument('--bundleIdentifier', help="bundle identifier for project")
  parser.add_argument('--certificate', help="certificate for project")
  parser.add_argument('--provisionProfile', help="provision profile for project")
  parser.add_argument('--team', help="team id for project")
  parser.add_argument('--exportType', help="export type for project (ad-hoc, development, app-store, enterprise)", default='ad-hoc')
  parser.add_argument('--archivePath', help="archive path for project", default='./output/app.xcarchive')
  parser.add_argument('--exportOptionsPath', help="exportOptions path for project", default='./output/ExportOptions.plist')
  parser.add_argument('--exportPath', help="export path for project", default='./output/app/')
  parser.add_argument('--derivedDataPath', help="derivedData path for project", default='./build/')
  parser.add_argument('--uploadSymbols', help="uploadSymbols setting for project", action="store_true", default=True)
  parser.add_argument('--otherArgs', help="uploadSymbols setting for project", nargs='*')

  parser.add_argument('action', help="actions for xcodebuild (build, clean, archive, exportArchive)", choices=[BuildCommand.BUILD, BuildCommand.CLEAN, BuildCommand.ARCHIVE, BuildCommand.EXPORTARCHIVE])
  
  args = parser.parse_args()
  return args

if __name__ == '__main__':
  args = parseArguments()
  print(args.otherArgs)
  cmd = BuildCommand(args.action, targetName=args.target, projectName=args.project, workspaceName=args.workspace, scheme=args.scheme, configuration=args.configuration, bundleIdentifier=args.bundleIdentifier, certificationName=args.certificate, provisionProfileName=args.provisionProfile, teamId=args.team, exportType=args.exportType, archivePath=args.archivePath, exportPath=args.exportPath, exportOptionsPath=args.exportOptionsPath, derivedDataPath=args.derivedDataPath, uploadSymbols=args.uploadSymbols)
  if args.otherArgs and len(args.otherArgs) > 0:
    cmd.otherArgs = args.otherArgs
  exit(cmd.run())

  
