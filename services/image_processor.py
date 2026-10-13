import cv2
import numpy as np


# =====================================================
# REFERENCE COLORS
# WHITE → PALE YELLOW → YELLOW → LIGHT BROWN
# → DARK BROWN → BLACK
# =====================================================

REFERENCE_COLORS = {
    "LEVEL 1": np.array([255, 255, 255]),   # WHITE
    "LEVEL 2": np.array([255, 249, 196]),   # PALE YELLOW
    "LEVEL 3": np.array([255, 215, 0]),     # YELLOW
    "LEVEL 4": np.array([210, 180, 140]),   # LIGHT BROWN
    "LEVEL 5": np.array([139, 90, 43]),     # DARK BROWN
    "LEVEL 6": np.array([0, 0, 0])          # BLACK
}


PPM_LEVELS = {
    "LEVEL 1": {
        "color": "WHITE",
        "ppm": 0,
        "ppm_range": "0 ppm",
        "status": "SAFE",
        "message": "No H₂S response detected. The area is currently safe based on the strip reading."
    },
    "LEVEL 2": {
        "color": "PALE YELLOW",
        "ppm": 0.03,
        "ppm_range": "0.03–0.5 ppm",
        "status": "WARNING",
        "message": "A low H₂S response was detected. Stay alert and continue monitoring the area."
    },
    "LEVEL 3": {
        "color": "YELLOW",
        "ppm": 1,
        "ppm_range": "1–5 ppm",
        "status": "WARNING",
        "message": "H₂S may be present. Avoid unnecessary exposure and follow workplace safety procedures."
    },
    "LEVEL 4": {
        "color": "LIGHT BROWN",
        "ppm": 5,
        "ppm_range": "5–10 ppm",
        "status": "DANGER",
        "message": "A dangerous H₂S response was detected. Leave the area and alert your supervisor."
    },
    "LEVEL 5": {
        "color": "DARK BROWN",
        "ppm": 10,
        "ppm_range": "10–20 ppm",
        "status": "DANGER",
        "message": "High H₂S exposure is indicated. Evacuate immediately and follow emergency procedures."
    },
    "LEVEL 6": {
        "color": "BLACK",
        "ppm": 20,
        "ppm_range": "20+ ppm",
        "status": "DANGER",
        "message": "Extremely high H₂S exposure is indicated. Evacuate immediately; do not enter without proper protection."
    }
}


# =====================================================
# AUTOMATIC STRIP DETECTION
# =====================================================

def detect_strip_crop(image):
    """
    Automatically detects the indicator strip in the image.

    Returns:
        x, y, width, height

    If no suitable strip is found:
        returns None
    """

    if image is None:
        return None

    image_height, image_width = image.shape[:2]

    if image_width < 50 or image_height < 50:
        return None


    # -------------------------------------------------
    # Resize for faster processing
    # -------------------------------------------------

    scale = 1.0

    max_dimension = 1000

    if max(image_width, image_height) > max_dimension:

        scale = max_dimension / max(
            image_width,
            image_height
        )

        small = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale
        )

    else:

        small = image.copy()


    small_height, small_width = small.shape[:2]


    # -------------------------------------------------
    # Convert to grayscale
    # -------------------------------------------------

    gray = cv2.cvtColor(
        small,
        cv2.COLOR_BGR2GRAY
    )


    # -------------------------------------------------
    # Blur
    # -------------------------------------------------

    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )


    # -------------------------------------------------
    # Edge detection
    # -------------------------------------------------

    edges = cv2.Canny(
        blurred,
        40,
        140
    )


    # -------------------------------------------------
    # Morphological operation
    # Connect broken strip edges
    # -------------------------------------------------

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (7, 7)
    )

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )


    # -------------------------------------------------
    # Find contours
    # -------------------------------------------------

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    candidates = []


    # -------------------------------------------------
    # Analyze contours
    # -------------------------------------------------

    for contour in contours:

        area = cv2.contourArea(contour)

        if area < 500:
            continue


        x, y, w, h = cv2.boundingRect(
            contour
        )


        if w < 30 or h < 30:
            continue


        contour_area = float(area)

        rectangle_area = float(w * h)


        if rectangle_area <= 0:
            continue


        rectangularity = (
            contour_area /
            rectangle_area
        )


        aspect_ratio = max(w, h) / min(w, h)


        # -------------------------------------------------
        # A chemical indicator strip is normally elongated
        # -------------------------------------------------

        if aspect_ratio < 1.4:
            continue


        if aspect_ratio > 12:
            continue


        # -------------------------------------------------
        # Ignore objects occupying almost the entire image
        # -------------------------------------------------

        if w > small_width * 0.90:
            continue

        if h > small_height * 0.90:
            continue


        # -------------------------------------------------
        # Calculate saturation
        # Colored/brown/yellow strips have useful saturation
        # -------------------------------------------------

        hsv = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2HSV
        )


        roi = hsv[
            y:y + h,
            x:x + w
        ]


        if roi.size == 0:
            continue


        saturation = np.mean(
            roi[:, :, 1]
        )


        # -------------------------------------------------
        # Calculate darkness
        # -------------------------------------------------

        brightness = np.mean(
            roi[:, :, 2]
        )


        # -------------------------------------------------
        # Candidate score
        # -------------------------------------------------

        score = 0


        # Larger objects are preferred
        score += min(
            area / (small_width * small_height) * 100,
            30
        )


        # Rectangular objects are preferred
        score += rectangularity * 30


        # Prefer elongated objects
        if 1.8 <= aspect_ratio <= 8:
            score += 25

        elif 1.4 <= aspect_ratio < 1.8:
            score += 10


        # Colored strips are useful
        if saturation > 25:
            score += 15


        # Dark/brown strips are useful
        if brightness < 180:
            score += 10


        candidates.append(
            (
                score,
                x,
                y,
                w,
                h
            )
        )


    # -------------------------------------------------
    # If no candidates from edge detection,
    # try color/saturation detection
    # -------------------------------------------------

    if not candidates:

        hsv = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2HSV
        )


        # Detect colored regions
        saturation_mask = cv2.inRange(
            hsv[:, :, 1],
            30,
            255
        )


        kernel2 = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (9, 9)
        )


        saturation_mask = cv2.morphologyEx(
            saturation_mask,
            cv2.MORPH_CLOSE,
            kernel2,
            iterations=2
        )


        saturation_mask = cv2.morphologyEx(
            saturation_mask,
            cv2.MORPH_OPEN,
            kernel2
        )


        color_contours, _ = cv2.findContours(
            saturation_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )


        for contour in color_contours:

            area = cv2.contourArea(
                contour
            )

            if area < 500:
                continue


            x, y, w, h = cv2.boundingRect(
                contour
            )


            if w < 30 or h < 30:
                continue


            aspect_ratio = (
                max(w, h) /
                min(w, h)
            )


            if aspect_ratio < 1.4:
                continue


            if aspect_ratio > 12:
                continue


            rectangularity = (
                area /
                float(w * h)
            )


            score = (
                area /
                (small_width * small_height)
                * 100
            )


            score += rectangularity * 30


            if 1.8 <= aspect_ratio <= 8:
                score += 25


            candidates.append(
                (
                    score,
                    x,
                    y,
                    w,
                    h
                )
            )


    # -------------------------------------------------
    # No strip detected
    # -------------------------------------------------

    if not candidates:
        return None


    # -------------------------------------------------
    # Select best candidate
    # -------------------------------------------------

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )


    _, x, y, w, h = candidates[0]


    # -------------------------------------------------
    # Add small padding around strip
    # -------------------------------------------------

    padding_x = int(
        w * 0.05
    )

    padding_y = int(
        h * 0.05
    )


    x = max(
        0,
        x - padding_x
    )


    y = max(
        0,
        y - padding_y
    )


    w = min(
        small_width - x,
        w + (2 * padding_x)
    )


    h = min(
        small_height - y,
        h + (2 * padding_y)
    )


    # -------------------------------------------------
    # Convert coordinates back to original image size
    # -------------------------------------------------

    if scale != 1.0:

        x = int(x / scale)
        y = int(y / scale)
        w = int(w / scale)
        h = int(h / scale)


    # -------------------------------------------------
    # Final safety check
    # -------------------------------------------------

    x = max(
        0,
        min(x, image_width - 1)
    )

    y = max(
        0,
        min(y, image_height - 1)
    )

    w = min(
        w,
        image_width - x
    )

    h = min(
        h,
        image_height - y
    )


    if w < 20 or h < 20:
        return None


    return {
        "x": int(x),
        "y": int(y),
        "width": int(w),
        "height": int(h)
    }


# =====================================================
# APPLY CROP
# =====================================================

def apply_crop(image, crop):

    if image is None or crop is None:
        return image


    try:

        x = int(
            crop.get("x", 0)
        )

        y = int(
            crop.get("y", 0)
        )

        width = int(
            crop.get("width", 0)
        )

        height = int(
            crop.get("height", 0)
        )


        image_height, image_width = (
            image.shape[:2]
        )


        # Keep coordinates inside image
        x = max(
            0,
            min(
                x,
                image_width - 1
            )
        )


        y = max(
            0,
            min(
                y,
                image_height - 1
            )
        )


        width = min(
            width,
            image_width - x
        )


        height = min(
            height,
            image_height - y
        )


        if width > 10 and height > 10:

            return image[
                y:y + height,
                x:x + width
            ]


    except Exception:

        pass


    return image


# =====================================================
# ANALYZE STRIP IMAGE
# =====================================================

def analyze_strip(
    image_bytes,
    crop=None
):

    # -------------------------------------------------
    # Convert uploaded image to OpenCV image
    # -------------------------------------------------

    image_array = np.frombuffer(
        image_bytes,
        np.uint8
    )


    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )


    # -------------------------------------------------
    # Image error
    # -------------------------------------------------

    if image is None:

        return {

            "result": "UNKNOWN",

            "visual_level": "UNKNOWN",

            "ppm": None,

            "ppm_range": "Unavailable",

            "status": "UNKNOWN",

            "status_message": "The image could not be read. Please upload a clear strip image.",

            "response_level":
                "IMAGE ERROR",

            "confidence": 0,

            "dominant_color":
                "UNKNOWN"

        }


    # =================================================
    # AUTOMATIC STRIP DETECTION
    # =================================================

    automatic_crop = detect_strip_crop(
        image
    )


    # -------------------------------------------------
    # IMPORTANT:
    # Use automatically detected strip.
    # This means the user does not need to
    # manually select the strip.
    # -------------------------------------------------

    if automatic_crop:

        image = apply_crop(
            image,
            automatic_crop
        )


    # -------------------------------------------------
    # If automatic detection fails,
    # use manual crop only as fallback.
    # -------------------------------------------------

    elif crop:

        image = apply_crop(
            image,
            crop
        )


    # =================================================
    # RESIZE IMAGE
    # =================================================

    image = cv2.resize(
        image,
        (300, 200),
        interpolation=cv2.INTER_AREA
    )


    # =================================================
    # BGR → RGB
    # =================================================

    image_rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )


    # =================================================
    # REMOVE OUTER BORDER
    #
    # This helps avoid shadows/background around
    # the detected strip.
    # =================================================

    height, width = image_rgb.shape[:2]


    border_x = int(
        width * 0.08
    )

    border_y = int(
        height * 0.08
    )


    if (
        width > 50 and
        height > 50
    ):

        inner_image = image_rgb[
            border_y:height - border_y,
            border_x:width - border_x
        ]

    else:

        inner_image = image_rgb


    # =================================================
    # GET PIXELS
    # =================================================

    pixels = inner_image.reshape(
        -1,
        3
    )


    # =================================================
    # CALCULATE BRIGHTNESS
    # =================================================

    brightness = np.mean(
        pixels,
        axis=1
    )


    # -------------------------------------------------
    # Remove extreme pixels caused by
    # reflections and black borders
    # -------------------------------------------------

    useful_pixels = pixels[
        (brightness > 10) &
        (brightness < 252)
    ]


    if len(useful_pixels) < 100:

        useful_pixels = pixels


    # =================================================
    # MEDIAN COLOR
    # =================================================

    detected_rgb = np.median(
        useful_pixels,
        axis=0
    )


    # =================================================
    # FIND CLOSEST REFERENCE COLOR
    # =================================================

    best_level = None

    best_distance = float("inf")


    for level, reference in (
        REFERENCE_COLORS.items()
    ):

        distance = np.linalg.norm(
            detected_rgb -
            reference
        )


        if distance < best_distance:

            best_distance = distance

            best_level = level


    # =================================================
    # CONFIDENCE
    # =================================================

    confidence = max(
        0,
        min(
            99,
            int(
                100 -
                best_distance / 3
            )
        )
    )


    # =================================================
    # DOMINANT COLOR
    # =================================================

    dominant_color = get_color_name(
        detected_rgb
    )


    # =================================================
    # RETURN RESULT
    # =================================================

    return {

        "result":
            PPM_LEVELS[best_level]["status"],

        "visual_level":
            best_level,

        "ppm":
            PPM_LEVELS[best_level]["ppm"],

        "ppm_range":
            PPM_LEVELS[best_level]["ppm_range"],

        "status":
            PPM_LEVELS[best_level]["status"],

        "status_message":
            PPM_LEVELS[best_level]["message"],

        "response_level":
            get_response_description(
                best_level
            ),

        "confidence":
            confidence,

        "dominant_color":
            dominant_color

    }


# =====================================================
# COLOR NAME
# =====================================================

def get_color_name(rgb):

    r, g, b = rgb


    # =================================================
    # WHITE
    # =================================================

    if (
        r > 235 and
        g > 235 and
        b > 235
    ):

        return "WHITE"


    # =================================================
    # PALE YELLOW
    # =================================================

    if (
        r > 220 and
        g > 210 and
        b < 210 and
        r >= g and
        g > b + 15
    ):

        return "PALE YELLOW"


    # =================================================
    # YELLOW
    # =================================================

    if (
        r > 200 and
        g > 170 and
        b < 100 and
        r > b + 80
    ):

        return "YELLOW"


    # =================================================
    # LIGHT BROWN
    # =================================================

    if (
        r > 140 and
        g > 80 and
        g < 180 and
        b < 140 and
        r > g
    ):

        return "LIGHT BROWN"


    # =================================================
    # DARK BROWN
    # =================================================

    if (
        r >= 45 and
        r < 150 and
        g < 110 and
        b < 90 and
        r > g
    ):

        return "DARK BROWN"


    # =================================================
    # BLACK
    # =================================================

    if (
        r < 45 and
        g < 45 and
        b < 45
    ):

        return "BLACK"


    # =================================================
    # GREY
    # =================================================

    if (
        abs(r - g) < 18 and
        abs(g - b) < 18
    ):

        return "GREY"


    return "GREY / BROWN"


# =====================================================
# RESPONSE DESCRIPTION
# =====================================================

def get_response_description(level):

    descriptions = {

        "LEVEL 1":
            "LOW VISUAL RESPONSE",

        "LEVEL 2":
            "LOW-MODERATE VISUAL RESPONSE",

        "LEVEL 3":
            "MODERATE VISUAL RESPONSE",

        "LEVEL 4":
            "HIGH VISUAL RESPONSE",

        "LEVEL 5":
            "VERY HIGH VISUAL RESPONSE",

        "LEVEL 6":
            "STRONGEST VISUAL RESPONSE"

    }


    return descriptions.get(
        level,
        "UNKNOWN"
    )