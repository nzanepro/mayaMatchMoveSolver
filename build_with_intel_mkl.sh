PROJECT_ROOT=`pwd`


# Remove 
rm -R --force ${PROJECT_ROOT}/external/lib/*
rm -R --force ${PROJECT_ROOT}/external/include/*


# Build the external dependencies
sh external/build_levmar_with_mkl.sh
sh external/build_suitesparse_with_mkl.sh
sh external/build_sparselm_with_mkl.sh


# Build plugin
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DMAYA_INCLUDE_PATH=/usr/autodesk/maya2016/include \
      -DMAYA_LIB_PATH=/usr/autodesk/maya2016/lib \
      -DLEVMAR_LIB_PATH=${PROJECT_ROOT}/external/lib \
      -DLEVMAR_INCLUDE_PATH=${PROJECT_ROOT}/external/include \
      -DSPLM_LIB_PATH=${PROJECT_ROOT}/external/lib \
      -DSPLM_INCLUDE_PATH=${PROJECT_ROOT}/external/lib \
      -DSUITE_SPARSE_LIB_PATH=${PROJECT_ROOT}/external/lib \
      -DMKL_LIB_PATH=/opt/intel/mkl/lib/intel64 \
      -DHAVE_SPLM=1 \
      -DUSE_ATLAS=0 \
      -DUSE_MKL=1 \
      ..
make clean
make -j4

