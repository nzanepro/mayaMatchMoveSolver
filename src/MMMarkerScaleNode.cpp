/*
 * Simple computation node to keep markers in screen-space when the camera filmback/focal length is modified.
 */

#include <MMMarkerScaleNode.h>

#include <maya/MPlug.h>
#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnCompoundAttribute.h>

#include <utilities/debugUtils.h>
#include <utilities/numberUtils.h>

#include <cstring>
#include <cmath>

#include <nodeTypeIds.h>

#include <Camera.h>

MTypeId MMMarkerScaleNode::m_id(MM_MARKER_SCALE_TYPE_ID);

// Input Attributes
MObject MMMarkerScaleNode::a_focalLength;
MObject MMMarkerScaleNode::a_cameraAperture;
MObject MMMarkerScaleNode::a_horizontalFilmAperture;
MObject MMMarkerScaleNode::a_verticalFilmAperture;
MObject MMMarkerScaleNode::a_filmOffset;
MObject MMMarkerScaleNode::a_horizontalFilmOffset;
MObject MMMarkerScaleNode::a_verticalFilmOffset;
MObject MMMarkerScaleNode::a_depth;

// Output Attributes
MObject MMMarkerScaleNode::a_outTranslate;
MObject MMMarkerScaleNode::a_outTranslateX;
MObject MMMarkerScaleNode::a_outTranslateY;
MObject MMMarkerScaleNode::a_outTranslateZ;
MObject MMMarkerScaleNode::a_outScale;
MObject MMMarkerScaleNode::a_outScaleX;
MObject MMMarkerScaleNode::a_outScaleY;
MObject MMMarkerScaleNode::a_outScaleZ;

MMMarkerScaleNode::MMMarkerScaleNode() {}

MMMarkerScaleNode::~MMMarkerScaleNode() {}

MString MMMarkerScaleNode::nodeName() {
    return MString("mmMarkerScale");
}

MStatus MMMarkerScaleNode::compute(const MPlug &plug, MDataBlock &data) {
    MStatus status = MS::kUnknownParameter;

    if ((plug == a_outTranslate)
        || (plug == a_outTranslateX)
        || (plug == a_outTranslateY)
        || (plug == a_outTranslateZ)
        || (plug == a_outScale)
        || (plug == a_outScaleX)
        || (plug == a_outScaleY)
        || (plug == a_outScaleZ)) {
        // Get Data Handles
        MDataHandle focalLengthHandle = data.inputValue(a_focalLength);
        MDataHandle filmBackXHandle = data.inputValue(a_horizontalFilmAperture);
        MDataHandle filmBackYHandle = data.inputValue(a_verticalFilmAperture);
        MDataHandle filmBackOffsetXHandle = data.inputValue(a_horizontalFilmOffset);
        MDataHandle filmBackOffsetYHandle = data.inputValue(a_verticalFilmOffset);
        MDataHandle depthHandle = data.inputValue(a_depth);

        // Get value
        double focalLength = focalLengthHandle.asDouble();
        double filmBackX = filmBackXHandle.asDouble() * INCH_TO_MM;
        double filmBackY = filmBackYHandle.asDouble() * INCH_TO_MM;
        double filmBackOffsetX = filmBackOffsetXHandle.asDouble() * INCH_TO_MM;
        double filmBackOffsetY = filmBackOffsetYHandle.asDouble() * INCH_TO_MM;
        double depth = depthHandle.asDouble();

        double scale = 0.0;
        getCameraPlaneScale(filmBackX, focalLength, scale);

        double translateX = scale * depth * (filmBackOffsetX/(filmBackX * 0.5));
        double translateY = scale * depth * (filmBackOffsetY/(filmBackY * 0.5)) * (filmBackY/filmBackX);
        double translateZ = 0.0;

        double scaleX = scale * depth * 2.0;
        double scaleY = scale * depth * 2.0 * (filmBackY/filmBackX);
        double scaleZ = depth;

        // Output Translate
        MDataHandle outTranslateXHandle = data.outputValue(a_outTranslateX);
        MDataHandle outTranslateYHandle = data.outputValue(a_outTranslateY);
        MDataHandle outTranslateZHandle = data.outputValue(a_outTranslateZ);
        outTranslateXHandle.setDouble(translateX);
        outTranslateYHandle.setDouble(translateY);
        outTranslateZHandle.setDouble(translateZ);
        outTranslateXHandle.setClean();
        outTranslateYHandle.setClean();
        outTranslateZHandle.setClean();

        // Output Scale
        MDataHandle outScaleXHandle = data.outputValue(a_outScaleX);
        MDataHandle outScaleYHandle = data.outputValue(a_outScaleY);
        MDataHandle outScaleZHandle = data.outputValue(a_outScaleZ);
        outScaleXHandle.setDouble(scaleX);
        outScaleYHandle.setDouble(scaleY);
        outScaleZHandle.setDouble(scaleZ);
        outScaleXHandle.setClean();
        outScaleYHandle.setClean();
        outScaleZHandle.setClean();

        status = MS::kSuccess;
    }
    return status;
}

void *MMMarkerScaleNode::creator() {
    return (new MMMarkerScaleNode());
}

MStatus MMMarkerScaleNode::initialize() {
    MStatus status;
    MFnNumericAttribute numericAttr;
    MFnCompoundAttribute compoundAttr;

    // Focal Length (millimetres)
    a_focalLength = numericAttr.create(
            "focalLength", "fl",
            MFnNumericData::kDouble, 35.0);
    CHECK_MSTATUS(numericAttr.setStorable(true));
    CHECK_MSTATUS(numericAttr.setKeyable(true));
    CHECK_MSTATUS(addAttribute(a_focalLength));

    // Horizontal Film Aperture (inches)
    a_horizontalFilmAperture = numericAttr.create(
            "horizontalFilmAperture", "hfa",
            MFnNumericData::kDouble, 1.41732);
    CHECK_MSTATUS(numericAttr.setStorable(true));
    CHECK_MSTATUS(numericAttr.setKeyable(true));

    // Vertical Film Aperture (inches)
    a_verticalFilmAperture = numericAttr.create(
            "verticalFilmAperture", "vfa",
            MFnNumericData::kDouble, 0.94488);
    CHECK_MSTATUS(numericAttr.setStorable(true));
    CHECK_MSTATUS(numericAttr.setKeyable(true));

    // Film Offset (parent of filmOffset* attributes)
    a_cameraAperture = compoundAttr.create("cameraAperture", "cap", &status);
    CHECK_MSTATUS(status);
    compoundAttr.addChild(a_horizontalFilmAperture);
    compoundAttr.addChild(a_verticalFilmAperture);
    CHECK_MSTATUS(addAttribute(a_cameraAperture));

    // Horizontal Film Offset (inches)
    a_horizontalFilmOffset = numericAttr.create(
            "horizontalFilmOffset", "hfo",
            MFnNumericData::kDouble, 0.0);
    CHECK_MSTATUS(numericAttr.setStorable(true));
    CHECK_MSTATUS(numericAttr.setKeyable(true));

    // Vertical Film Offset (inches)
    a_verticalFilmOffset = numericAttr.create(
            "verticalFilmOffset", "vfo",
            MFnNumericData::kDouble, 0.0);
    CHECK_MSTATUS(numericAttr.setStorable(true));
    CHECK_MSTATUS(numericAttr.setKeyable(true));

    // Film Offset (parent of filmOffset* attributes)
    a_filmOffset = compoundAttr.create("filmOffset", "fio", &status);
    CHECK_MSTATUS(status);
    compoundAttr.addChild(a_horizontalFilmOffset);
    compoundAttr.addChild(a_verticalFilmOffset);
    CHECK_MSTATUS(addAttribute(a_filmOffset));

    // Depth
    a_depth = numericAttr.create(
            "depth", "dpt",
            MFnNumericData::kDouble, 1.0);
    CHECK_MSTATUS(numericAttr.setStorable(true));
    CHECK_MSTATUS(numericAttr.setKeyable(true));
    CHECK_MSTATUS(addAttribute(a_depth));

    // Out Translate X
    a_outTranslateX = numericAttr.create(
            "outTranslateX", "otx",
            MFnNumericData::kDouble, 0.0);
    CHECK_MSTATUS(numericAttr.setStorable(false));
    CHECK_MSTATUS(numericAttr.setKeyable(false));
    CHECK_MSTATUS(numericAttr.setReadable(true));
    CHECK_MSTATUS(numericAttr.setWritable(false));

    // Out Translate Y
    a_outTranslateY = numericAttr.create(
            "outTranslateY", "oty",
            MFnNumericData::kDouble, 0.0);
    CHECK_MSTATUS(numericAttr.setStorable(false));
    CHECK_MSTATUS(numericAttr.setKeyable(false));
    CHECK_MSTATUS(numericAttr.setReadable(true));
    CHECK_MSTATUS(numericAttr.setWritable(false));

    // Out Translate Z
    a_outTranslateZ = numericAttr.create(
            "outTranslateZ", "otz",
            MFnNumericData::kDouble, 0.0, &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(numericAttr.setStorable(false));
    CHECK_MSTATUS(numericAttr.setKeyable(false));
    CHECK_MSTATUS(numericAttr.setReadable(true));
    CHECK_MSTATUS(numericAttr.setWritable(false));

    // Out Translate (parent of outTranslate* attributes)
    a_outTranslate = compoundAttr.create("outTranslate", "ot", &status);
    CHECK_MSTATUS(status);
    compoundAttr.addChild(a_outTranslateX);
    compoundAttr.addChild(a_outTranslateY);
    compoundAttr.addChild(a_outTranslateZ);
    CHECK_MSTATUS(addAttribute(a_outTranslate));

    // Out Scale X
    a_outScaleX = numericAttr.create(
            "outScaleX", "osx",
            MFnNumericData::kDouble, 1.0);
    CHECK_MSTATUS(numericAttr.setStorable(false));
    CHECK_MSTATUS(numericAttr.setKeyable(false));
    CHECK_MSTATUS(numericAttr.setReadable(true));
    CHECK_MSTATUS(numericAttr.setWritable(false));

    // Out Scale Y
    a_outScaleY = numericAttr.create(
            "outScaleY", "osy",
            MFnNumericData::kDouble, 1.0);
    CHECK_MSTATUS(numericAttr.setStorable(false));
    CHECK_MSTATUS(numericAttr.setKeyable(false));
    CHECK_MSTATUS(numericAttr.setReadable(true));
    CHECK_MSTATUS(numericAttr.setWritable(false));

    // Out Scale Z
    a_outScaleZ = numericAttr.create(
            "outScaleZ", "osz",
            MFnNumericData::kDouble, 1.0, &status);
    CHECK_MSTATUS(status);
    CHECK_MSTATUS(numericAttr.setStorable(false));
    CHECK_MSTATUS(numericAttr.setKeyable(false));
    CHECK_MSTATUS(numericAttr.setReadable(true));
    CHECK_MSTATUS(numericAttr.setWritable(false));

    // Out Scale (parent of outScale* attributes)
    a_outScale = compoundAttr.create("outScale", "os", &status);
    CHECK_MSTATUS(status);
    compoundAttr.addChild(a_outScaleX);
    compoundAttr.addChild(a_outScaleY);
    compoundAttr.addChild(a_outScaleZ);
    CHECK_MSTATUS(addAttribute(a_outScale));

    // Attribute Affects
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_focalLength, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_cameraAperture, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmAperture, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmAperture, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_filmOffset, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_horizontalFilmOffset, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_verticalFilmOffset, a_outScaleZ));

    CHECK_MSTATUS(attributeAffects(a_depth, a_outTranslate));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outTranslateX));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outTranslateY));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outTranslateZ));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outScale));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outScaleX));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outScaleY));
    CHECK_MSTATUS(attributeAffects(a_depth, a_outScaleZ));

    return (MS::kSuccess);
}
