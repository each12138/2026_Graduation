# Install script for directory: /home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/unitree_pkgs/go2_sport_api

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/install/go2_sport_api")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include" TYPE DIRECTORY FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/unitree_pkgs/go2_sport_api/include")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api" TYPE EXECUTABLE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/vel_ctrl")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl"
         OLD_RPATH "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/unitree_pkgs/go2_sport_api/src:/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/install/unitree_go/lib:/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/install/unitree_api/lib:/opt/ros/foxy/lib:"
         NEW_RPATH "")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/go2_sport_api/vel_ctrl")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  include("/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/CMakeFiles/vel_ctrl.dir/install-cxx-module-bmi-noconfig.cmake" OPTIONAL)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/libgo2_sport_api.so")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so"
         OLD_RPATH "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/unitree_pkgs/go2_sport_api/src:/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/install/unitree_go/lib:/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/install/unitree_api/lib:/opt/ros/foxy/lib:"
         NEW_RPATH "")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libgo2_sport_api.so")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/environment" TYPE FILE FILES "/opt/ros/foxy/lib/python3.8/site-packages/ament_package/template/environment_hook/library_path.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/environment" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/library_path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/package_run_dependencies" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_index/share/ament_index/resource_index/package_run_dependencies/go2_sport_api")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/parent_prefix_path" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_index/share/ament_index/resource_index/parent_prefix_path/go2_sport_api")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/environment" TYPE FILE FILES "/opt/ros/foxy/share/ament_cmake_core/cmake/environment_hooks/environment/ament_prefix_path.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/environment" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/ament_prefix_path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/environment" TYPE FILE FILES "/opt/ros/foxy/share/ament_cmake_core/cmake/environment_hooks/environment/path.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/environment" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/path.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/local_setup.bash")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/local_setup.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/local_setup.zsh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/local_setup.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_environment_hooks/package.dsv")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/ament_index/resource_index/packages" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_index/share/ament_index/resource_index/packages/go2_sport_api")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake/export_go2_sport_apiExport.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake/export_go2_sport_apiExport.cmake"
         "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/CMakeFiles/Export/6254cf495a5041e5afac0eb2f65ce81a/export_go2_sport_apiExport.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake/export_go2_sport_apiExport-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake/export_go2_sport_apiExport.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/CMakeFiles/Export/6254cf495a5041e5afac0eb2f65ce81a/export_go2_sport_apiExport.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^()$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/CMakeFiles/Export/6254cf495a5041e5afac0eb2f65ce81a/export_go2_sport_apiExport-noconfig.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_export_dependencies/ament_cmake_export_dependencies-extras.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_export_libraries/ament_cmake_export_libraries-extras.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_export_include_directories/ament_cmake_export_include_directories-extras.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_export_targets/ament_cmake_export_targets-extras.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api/cmake" TYPE FILE FILES
    "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_core/go2_sport_apiConfig.cmake"
    "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/ament_cmake_core/go2_sport_apiConfig-version.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/go2_sport_api" TYPE FILE FILES "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/unitree_pkgs/go2_sport_api/package.xml")
endif()

if(CMAKE_INSTALL_COMPONENT)
  if(CMAKE_INSTALL_COMPONENT MATCHES "^[a-zA-Z0-9_.+-]+$")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
  else()
    string(MD5 CMAKE_INST_COMP_HASH "${CMAKE_INSTALL_COMPONENT}")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INST_COMP_HASH}.txt")
    unset(CMAKE_INST_COMP_HASH)
  endif()
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
  file(WRITE "/home/unitree/2026_Graduation/2026_Graduation/src/go2_ros2_toolbox_division_llm/build/go2_sport_api/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
