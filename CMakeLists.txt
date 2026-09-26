cmake_minimum_required(VERSION 3.20)

project(KadokaTetrisAI LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(kadoka_tetris_core
    core/src/active_piece.cpp
    core/src/board.cpp
    core/src/combat_rules.cpp
    core/src/game_state.cpp
    core/src/seven_bag.cpp
    core/src/tetromino.cpp
)

target_include_directories(kadoka_tetris_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/core/include
)

target_compile_features(kadoka_tetris_core PUBLIC cxx_std_20)

add_library(kadoka_tetris_runtime
    runtime/src/headless_runtime.cpp
)

target_include_directories(kadoka_tetris_runtime
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/runtime/include
)

target_link_libraries(kadoka_tetris_runtime PUBLIC kadoka_tetris_core)

target_compile_features(kadoka_tetris_runtime PUBLIC cxx_std_20)

include(CTest)

if(BUILD_TESTING)
    add_executable(kadoka_tetris_core_tests
        tests_cpp/core_board_test.cpp
    )
    target_link_libraries(kadoka_tetris_core_tests PRIVATE kadoka_tetris_core)
    add_test(NAME kadoka_tetris_core_tests COMMAND kadoka_tetris_core_tests)

    add_executable(kadoka_tetris_game_state_tests
        tests_cpp/game_state_test.cpp
    )
    target_link_libraries(kadoka_tetris_game_state_tests PRIVATE kadoka_tetris_core)
    add_test(NAME kadoka_tetris_game_state_tests COMMAND kadoka_tetris_game_state_tests)

    add_executable(kadoka_tetris_headless_runtime_tests
        tests_cpp/headless_runtime_test.cpp
    )
    target_link_libraries(kadoka_tetris_headless_runtime_tests PRIVATE kadoka_tetris_runtime)
    add_test(NAME kadoka_tetris_headless_runtime_tests COMMAND kadoka_tetris_headless_runtime_tests)
endif()
