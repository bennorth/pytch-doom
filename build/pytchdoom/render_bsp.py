import math

from pytchdoom.pddata_generated import *

########################################################################

ROOT_BSP_NODE_IDX = len(map_nodes) - 1
dbg_n_nodes = 0
dbg_n_ssectors = 0


########################################################################


def unit_along(seg):
    v1 = map_vertexes[seg[K_SEG_VX1]]
    v2 = map_vertexes[seg[K_SEG_VX2]]
    ax = v2[K_VERTEX_X] - v1[K_VERTEX_X]
    ay = v2[K_VERTEX_Y] - v1[K_VERTEX_Y]
    alen = math.hypot(ax, ay)
    return (ax / alen, ay / alen)


def unit_normal(seg):
    # Could we replace this with trusting the angle which is already stored in
    # the segment?
    v1 = map_vertexes[seg[K_SEG_VX1]]
    v2 = map_vertexes[seg[K_SEG_VX2]]
    nx = v1[K_VERTEX_Y] - v2[K_VERTEX_Y]
    ny = v2[K_VERTEX_X] - v1[K_VERTEX_X]
    nlen = math.hypot(nx, ny)
    return (nx / nlen, ny / nlen)


########################################################################

math_atan2 = math.atan2
math_atan = math.atan
math_sin = math.sin
math_cos = math.cos
math_tan = math.tan
math_floor = math.floor

########################################################################

for s in map_segs:
    s.extend(unit_along(s))
    s.extend(unit_normal(s))
    s.append(math_atan2(s[K_SEG_NORMAL_Y], s[K_SEG_NORMAL_X]))

########################################################################

DEBUG_PRINTS = True
DEBUG_PRINTS = False

M_PI = math.pi
TWO_PI = 2.0 * math.pi

FOCAL_LENGTH = 160.0
VIEWPLANE_WIDTH = 320.0
HALF_VIEWPLANE_WIDTH = VIEWPLANE_WIDTH * 0.5

# We know this is 45deg, but compute it anyway.
HALF_FIELD_OF_VIEW = math.atan(HALF_VIEWPLANE_WIDTH / FOCAL_LENGTH)

SCREEN_WIDTH = 320
HALF_SCREEN_WIDTH = 160
SCREEN_HEIGHT = 240

########################################################################


kSpanBehind = object()
kSpanOutOfView = object()


FACING_CMP_EPS = 1.0e-15


def facing_maybe_clamp(th1: float, th2: float):
    span = th1 - th2
    if span < 0.0:
        span += TWO_PI
    if span >= M_PI - FACING_CMP_EPS:
        return kSpanBehind

    if th1 < 0.0 and th2 > -th1:
        th2 -= TWO_PI
    if th2 > HALF_FIELD_OF_VIEW:
        return kSpanOutOfView

    if th2 > 0.0 and th1 < -th2:
        th1 += TWO_PI
    if th1 < -HALF_FIELD_OF_VIEW:
        return kSpanOutOfView

    if th1 > HALF_FIELD_OF_VIEW:
        th1 = HALF_FIELD_OF_VIEW
    if th2 < -HALF_FIELD_OF_VIEW:
        th2 = -HALF_FIELD_OF_VIEW

    return th1, th2


########################################################################


VIEW_POSE_N_STEPS = 96


class ViewPose:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.th_steps = VIEW_POSE_N_STEPS // 4
        self.th = TWO_PI * self.th_steps / VIEW_POSE_N_STEPS

    def click_turn_positive(self):
        self.th_steps += 1
        self.th_steps %= VIEW_POSE_N_STEPS
        self.th = TWO_PI * self.th_steps / VIEW_POSE_N_STEPS

    def click_turn_negative(self):
        self.th_steps -= 1
        self.th_steps %= VIEW_POSE_N_STEPS
        self.th = TWO_PI * self.th_steps / VIEW_POSE_N_STEPS

    def rel_angle_looking_at(self, x, y):
        dx = x - self.x
        dy = y - self.y
        abs_th = math_atan2(dy, dx)
        rel_th = (abs_th - self.th) % TWO_PI
        if rel_th >= M_PI:
            rel_th -= TWO_PI
        return rel_th

    def limit_angles(self, seg):
        v1 = map_vertexes[seg[K_SEG_VX1]]
        v2 = map_vertexes[seg[K_SEG_VX2]]
        th1 = self.rel_angle_looking_at(v1[K_VERTEX_X], v1[K_VERTEX_Y])
        th2 = self.rel_angle_looking_at(v2[K_VERTEX_X], v2[K_VERTEX_Y])
        return th1, th2

    def full_seg_span(self, seg):
        th1, th2 = self.limit_angles(seg)
        return int(viewangle_to_x(th1) + 0.5), int(viewangle_to_x(th2) + 0.5)

    def normal_projection(self, seg):
        n_x, n_y = seg[K_SEG_NORMAL_X], seg[K_SEG_NORMAL_Y]
        v1 = map_vertexes[seg[K_SEG_VX1]]
        v_to_v1_x = v1[K_VERTEX_X] - self.x
        v_to_v1_y = v1[K_VERTEX_Y] - self.y
        return v_to_v1_x * n_x + v_to_v1_y * n_y

    def along_projection_to_v1(self, seg):
        a_x, a_y = seg[K_SEG_TANGENT_X], seg[K_SEG_TANGENT_Y]
        v1 = map_vertexes[seg[K_SEG_VX1]]
        v_to_v1_x = v1[K_VERTEX_X] - self.x
        v_to_v1_y = v1[K_VERTEX_Y] - self.y
        return v_to_v1_x * a_x + v_to_v1_y * a_y

    def prepare_seg(self, seg):
        self.seg_normal_projection = self.normal_projection(seg)
        self.seg_along_projn_to_v1 = self.along_projection_to_v1(seg)
        self.seg_normal_th_minus_self_th = seg[K_SEG_NORMAL_TH] - self.th

    def offset_along(self, screen_th):
        ph = self.seg_normal_th_minus_self_th - screen_th
        return (
            self.seg_normal_projection * math_tan(ph)
            - self.seg_along_projn_to_v1
        )


########################################################################


def front_or_back(node, view_x, view_y):
    left = node[K_NODE_YT] * (view_x - node[K_NODE_X0])
    right = (view_y - node[K_NODE_Y0]) * node[K_NODE_XT]
    if right < left:
        return 0
    else:
        return 1


########################################################################


def viewangle_to_x(th):
    # Bigger angles correspond to smaller X-coords
    return int(HALF_VIEWPLANE_WIDTH - FOCAL_LENGTH * math_tan(th))


def x_to_viewangle_(x):
    # Flip because smaller x is moving leftwards which is sweeping ray
    # anticlockwise which is positive.
    centred_x = HALF_VIEWPLANE_WIDTH - x
    return math_atan(centred_x / FOCAL_LENGTH)


x_to_viewangle = [x_to_viewangle_(x) for x in range(SCREEN_WIDTH)]


########################################################################


class ClipRange:
    def __init__(self, lb, ub):
        self.lb = lb  # Inclusive
        self.ub = ub  # Exclusive


########################################################################

dbg_n_segs_drawn = 0
dbg_n_segs_skipped = 0


class RenderContext:
    def __init__(self, view_pose):
        self.view_pose = view_pose
        self.clip_ranges = [
            ClipRange(-100000, 0),
            ClipRange(int(VIEWPLANE_WIDTH), int(100 * VIEWPLANE_WIDTH)),
        ]
        self.screen_img = [None for _ in range(SCREEN_WIDTH)]

    def run(self):
        global dbg_n_segs_drawn
        global dbg_n_segs_skipped
        dbg_n_segs_drawn = 0
        dbg_n_segs_skipped = 0
        self.walk_bsp(ROOT_BSP_NODE_IDX)
        return self.screen_img

    def walk_bsp(self, node_idx):
        if node_idx >= 32768:
            # Special case for 65535?
            ssec_idx = node_idx - 32768
            ssec = map_ssectors[ssec_idx]
            self.render_subsector(ssec)
        else:
            bsp_node = map_nodes[node_idx]
            side = front_or_back(bsp_node, self.view_pose.x, self.view_pose.y)
            if DEBUG_PRINTS:
                print(
                    f"walk_bsp(): considering node[{node_idx}]"
                    f" ({bsp_node[K_NODE_X0]}, {bsp_node[K_NODE_Y0]})"
                    f" vec({bsp_node[K_NODE_XT]}, {bsp_node[K_NODE_YT]})"
                    f" {'FR' if side==0 else 'BK'}"
                )
            if side == 0:
                self.walk_bsp(bsp_node[K_NODE_R_IDX])
                if self.bbox_might_be_visible(
                    [
                        bsp_node[K_NODE_L_BBOX_T],
                        bsp_node[K_NODE_L_BBOX_B],
                        bsp_node[K_NODE_L_BBOX_L],
                        bsp_node[K_NODE_L_BBOX_R],
                    ]
                ):
                    self.walk_bsp(bsp_node[K_NODE_L_IDX])
                else:
                    if DEBUG_PRINTS:
                        print(
                            f"left bbox of node[{node_idx}] not visible"
                            f" so skipping node[{bsp_node[K_NODE_L_IDX]}]"
                        )
            else:
                self.walk_bsp(bsp_node[K_NODE_L_IDX])
                if self.bbox_might_be_visible(
                    [
                        bsp_node[K_NODE_R_BBOX_T],
                        bsp_node[K_NODE_R_BBOX_B],
                        bsp_node[K_NODE_R_BBOX_L],
                        bsp_node[K_NODE_R_BBOX_R],
                    ]
                ):
                    self.walk_bsp(bsp_node[K_NODE_R_IDX])
                else:
                    if DEBUG_PRINTS:
                        print(
                            f"right bbox of node[{node_idx}] not visible"
                            f" so skipping node[{bsp_node[K_NODE_R_IDX]}]"
                        )

    def bbox_might_be_visible(self, bbox: list[float]) -> bool:
        """
        bbox should have four elements:
            [0] = max y coord ("top")
            [1] = min y coord ("bottom")
            [2] = min x coord ("left")
            [3] = max x coord ("right")
        This order matches that used in R_CheckBBox() in Doom C code.
        """
        view_x = self.view_pose.x
        view_y = self.view_pose.y

        if view_x <= bbox[2]:
            box_x = 0
        elif view_x < bbox[3]:
            box_x = 1
        else:
            box_x = 2

        if view_y >= bbox[0]:
            box_y = 0
        elif view_y > bbox[1]:
            box_y = 1
        else:
            box_y = 2

        box_pos = box_y * 4 + box_x

        # Doom C code does this with a LUT; try this for now.
        if box_pos == 0:
            x1, y1, x2, y2 = bbox[3], bbox[0], bbox[2], bbox[1]
        elif box_pos == 1:
            x1, y1, x2, y2 = bbox[3], bbox[0], bbox[2], bbox[0]
        elif box_pos == 2:
            x1, y1, x2, y2 = bbox[3], bbox[1], bbox[2], bbox[0]
        #
        elif box_pos == 4:
            x1, y1, x2, y2 = bbox[2], bbox[0], bbox[2], bbox[1]
        elif box_pos == 5:
            return True
        elif box_pos == 6:
            x1, y1, x2, y2 = bbox[3], bbox[1], bbox[3], bbox[0]
        #
        elif box_pos == 8:
            x1, y1, x2, y2 = bbox[2], bbox[0], bbox[3], bbox[1]
        elif box_pos == 9:
            x1, y1, x2, y2 = bbox[2], bbox[1], bbox[3], bbox[1]
        elif box_pos == 10:
            x1, y1, x2, y2 = bbox[2], bbox[1], bbox[3], bbox[0]
        #
        else:
            # Really should not happen
            raise RuntimeError("bad box pos")

        th1 = self.view_pose.rel_angle_looking_at(x1, y1)
        th2 = self.view_pose.rel_angle_looking_at(x2, y2)

        clamped = facing_maybe_clamp(th1, th2)

        if DEBUG_PRINTS:
            print(
                f"bbox limits: x1={x1} y1={y1} x2={x2} y2={y2};"
                f" view point x={view_x} y={view_y}\n"
                f"radian angles: th1={th1} th2={th2}"
                f" th2-th1={th2-th1} th2-th1-pi={th2-th1-math.pi}\n"
                f"th1={math.degrees(th1):.1f} th2={math.degrees(th2):.1f}"
                f" clamped={clamped}"
            )

        if clamped is kSpanBehind:
            return True

        if clamped is kSpanOutOfView:
            return False

        th1, th2 = clamped
        sx_lb = viewangle_to_x(th1)
        sx_ub = viewangle_to_x(th2)

        # Very tiny, so don't bother:
        if sx_ub == sx_lb:
            return False

        # Find the first clip-range whose leftwards extension includes the
        # bbox-span.  If the bbox-span protrudes to the left of that clip-
        # -range, we might be able to see the bbox.
        for clip_range in self.clip_ranges:
            if clip_range.ub >= sx_ub:
                if DEBUG_PRINTS:
                    print(f"cliprange {clip_range} cf lb={sx_lb} ub={sx_ub}")
                return sx_lb < clip_range.lb

        raise RuntimeError(
            f"should have found clip-range for"
            f" th1={math.degrees(th1):.1f} th2={math.degrees(th2):.1f}"
            f" sx_ub={sx_ub} in {self.clip_ranges}"
        )

    def render_wall_fragment(self, x0: int, x1: int):
        if DEBUG_PRINTS:
            print(f"      render_wall_fragment(): [{x0}, {x1})")
        x_scale = self.seg_scale_0 + (x0 - self.seg_x0) * self.seg_dscale
        offset_along = self.view_pose.offset_along
        offset_0 = self.seg_draw_seg[K_SEG_OFFSET]
        for x in range(x0, x1):
            screen_th = x_to_viewangle[x]
            raw_tex_col = offset_0 + offset_along(screen_th)
            tex_col = int(raw_tex_col + 0.5)

            self.screen_img[x] = [self.seg_tx_mid, tex_col, x_scale]

            x_scale += self.seg_dscale

    def render_subsector(self, ssec):
        global dbg_n_segs_drawn
        global dbg_n_segs_skipped
        if DEBUG_PRINTS:
            print(f"render_subsector(): {ssec}")

        # "-1" because we increment as first job inside loop to avoid confusion
        # with all the "continue" statements.
        seg_idx = ssec[K_SSECTOR_IDX0] - 1
        n_segs = ssec[K_SSECTOR_NSEGS]
        while n_segs > 0:
            seg_idx += 1
            n_segs -= 1
            seg = map_segs[seg_idx]

            # Relative viewing angles to the two endpoints, i.e., how far would
            # the player need to rotate their head anticlockwise from their
            # current pose to be looking straight at each vertex.
            th1, th2 = self.view_pose.limit_angles(seg)
            clamped = facing_maybe_clamp(th1, th2)

            if DEBUG_PRINTS:
                print(
                    f"  considering seg[{seg_idx}] {seg}"
                    f" th1={math.degrees(th1):.1f}"
                    f" th2={math.degrees(th2):.1f}"
                    f" clamped={clamped}\n"
                    f" "
                )

            if clamped is kSpanBehind or clamped is kSpanOutOfView:
                if DEBUG_PRINTS:
                    print(f"    skipping 'behind' or 'out-of-view' seg")
                continue

            dbg_n_segs_drawn += 1

            th1, th2 = clamped

            # Seg is at least partially in view.
            sx_lb = int(viewangle_to_x(th1) + 0.5)
            sx_ub = int(viewangle_to_x(th2) + 0.5)

            if sx_ub == sx_lb:
                if DEBUG_PRINTS:
                    print(f"    skipping 'teeny-tiny' seg")
                continue

            self.view_pose.prepare_seg(seg)

            seg_normal_angle = seg[K_SEG_NORMAL_TH]
            seg_norm_proj = self.view_pose.seg_normal_projection

            # Recall th1 and th2 are already relative to view-pose angle.

            angle_a1 = th1
            angle_b1 = th1 - seg_normal_angle + self.view_pose.th

            angle_a2 = th2
            angle_b2 = th2 - seg_normal_angle + self.view_pose.th

            cos_b1 = math_cos(angle_b1)
            cos_b2 = math_cos(angle_b2)

            scale_1 = (
                4.0
                if seg_norm_proj < cos_b1
                else (
                    FOCAL_LENGTH * cos_b1
                    / (seg_norm_proj * math_cos(angle_a1))
                )
            )

            scale_2 = (
                4.0
                if seg_norm_proj < cos_b2
                else (
                    FOCAL_LENGTH * cos_b2
                    / (seg_norm_proj * math_cos(angle_a2))
                )
            )

            if DEBUG_PRINTS:
                print(
                    f"    computed normdist={seg_normal_distance:.1f};",
                    f" poseangle={math.degrees(self.view_pose.th):.1f};",
                    f" normalangle={math.degrees(seg_normal_angle):.1f};",
                    f" a1={math.degrees(angle_a1):.1f};"
                    f" b1={math.degrees(angle_b1):.1f};",
                    f" scale_1={scale_1:.4f};",
                    f" a2={math.degrees(angle_a2):.1f};"
                    f" b2={math.degrees(angle_b2):.1f};",
                    f" scale_2={scale_2:.4f}",
                )

            self.seg_scale_0 = scale_1
            self.seg_dscale = (scale_2 - scale_1) / (sx_ub - sx_lb)
            self.seg_x0 = sx_lb

            self.render_partial_seg(seg, sx_lb, sx_ub)

    def render_partial_seg(self, draw_seg, sx_lb, sx_ub):
        # Roughly equivalent to R_AddLine() in CDoom.

        if DEBUG_PRINTS:
            print(f"    render_seg()")

        self.seg_draw_seg = draw_seg
        self.seg_tx_mid = draw_seg[K_SEG_FRONT_TX]

        # Find first clip-range with the property that the union of its left
        # extension with the wall-seg is connected.  This happens when the ub of
        # the clip-range matches or is to the right of the lb of the wall-seg.
        #
        # The final clip-range should be a "catch-all" with an "infinite" ub,
        # but we were seeing seg_x0 values much bigger.  Might improve if we
        # clip angles before mapping to screen?
        clip_range_idx = 0
        idx_ub = len(self.clip_ranges) - 1
        while (
            clip_range_idx < idx_ub
            and self.clip_ranges[clip_range_idx].ub < sx_lb
        ):
            clip_range_idx += 1

        start_clip_range_idx = clip_range_idx
        start_clip_range = self.clip_ranges[clip_range_idx]

        # Is there at least a portion of the wall-seg to the left of this (now
        # non-extended) clip-range?
        if sx_lb < start_clip_range.lb:
            # Is in fact the entire wall-seg *strictly* to the left of this
            # clip-range?
            if sx_ub < start_clip_range.lb:
                # Yes, draw the whole thing, insert a clip-range
                # matching the wall-seg, and we're done.
                self.render_wall_fragment(sx_lb, sx_ub)
                self.clip_ranges.insert(clip_range_idx, ClipRange(sx_lb, sx_ub))
                return

            # There is a fragment of the wall-seg (or possibly the entire
            # wall-seg, abutting) to the left of the clip-range.  Draw it and
            # extend the clip-range leftwards.
            self.render_wall_fragment(sx_lb, start_clip_range.lb)
            start_clip_range.lb = sx_lb

        # If the wall-seg does not extend to the right of the clip-range, we're
        # done.
        if sx_ub <= start_clip_range.ub:
            return

        # Iterate over subsequent clip-ranges.
        wall_seg_ended_within_clip_range = False
        while sx_ub >= self.clip_ranges[clip_range_idx + 1].lb:
            self.render_wall_fragment(
                self.clip_ranges[clip_range_idx].ub,
                self.clip_ranges[clip_range_idx + 1].lb,
            )
            clip_range_idx += 1

            # If the wall-seg ends within the (just-advanced) "current"
            # clip-range, extend the "starting" clip-range rightwards and we're
            # done iterating.
            if sx_ub <= self.clip_ranges[clip_range_idx].ub:
                start_clip_range.ub = self.clip_ranges[clip_range_idx].ub
                wall_seg_ended_within_clip_range = True
                break

        # If the wall seg ended strictly between clip-ranges, render the part of
        # the wall-seg that extends to the right of the most recently considered
        # clip-range, and extend the "start" clip-range rightwards to note the
        # newly-rendered fragment.
        if not wall_seg_ended_within_clip_range:
            self.render_wall_fragment(
                self.clip_ranges[clip_range_idx].ub,
                sx_ub
            )
            start_clip_range.ub = sx_ub

        # The "start" clip-range now covers all rendering which has been done.
        # There might be some now-redundant clip-ranges strictly after the
        # "start" one.  Remove them.
        del_lb = start_clip_range_idx + 1
        del_ub = clip_range_idx + 1
        del self.clip_ranges[del_lb:del_ub]  # No-op if ub <= lb, as reqd
