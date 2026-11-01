import random

from pytch.syscalls import (
    push_loop_iterations_per_frame,
    pop_loop_iterations_per_frame,
)


HEIGHT_0 = 12.0
height_bob_ampl = 0.0
height_bob_ph = 0.0


class Post(pytch.Sprite):
    Costumes = []  # TO FILL

    @pytch.when_green_flag_clicked
    def make_clones(self):
        self.idx = 0
        push_loop_iterations_per_frame(320)
        for i in range(320):
            self.create_clone()
            self.idx += 1
        pop_loop_iterations_per_frame()
        self.hide()
        self.broadcast("init-render")
        self.broadcast_and_wait("play-intro")
        self.broadcast("run-game")

    @pytch.when_I_start_as_a_clone
    def set_posn(self):
        self.set_x(-HALF_SCREEN_WIDTH + self.idx + 0.5)

    @pytch.when_I_receive("render")
    def do_render(self):
        if self.idx < SCREEN_WIDTH:
            post = image_columns[self.idx]
            tx_id = post[0]
            if tx_id == 0:
                return
            costume_idx_0 = TX_DATA[tx_id]
            tx_wd = TX_DATA[tx_id + 1]
            raw_col = post[1]
            col = raw_col % tx_wd
            self.switch_costume(costume_idx_0 + col)
            self.set_size(post[2] * 1.2)
            self.set_y(post[2] * (height_bob_ampl * math_sin(height_bob_ph) - HEIGHT_0))


image_columns = []
view_pose = ViewPose(-1472, -3344)


class Background(pytch.Stage):
    Backdrops = ["gradient-bg.png"]


MAX_HEIGHT_BOB_AMPL = 12.0
HEIGHT_BOB_VEL = 0.5


class Control(pytch.Sprite):
    @pytch.when_green_flag_clicked
    def show_dbg(self):
        pass
        # pytch.show_variable(None, "dbg_n_segs_drawn")
        # pytch.show_variable(None, "dbg_n_segs_skipped", left=-80)

    @pytch.when_I_receive("init-render")
    def render(self):
        global image_columns
        render_ctx = RenderContext(view_pose)

        push_loop_iterations_per_frame(10000)
        image_columns = render_ctx.run()
        pop_loop_iterations_per_frame()

        pytch.broadcast("render")

    @pytch.when_I_receive("run-game")
    def run_loop(self):
        global height_bob_ampl
        global height_bob_ph
        while True:
            height_bob_ph += 0.2
            height_bob_ph %= M_PI
            new_loc = [view_pose.x, view_pose.y]
            move_attempt = False
            if self.key_pressed("ArrowLeft"):
                view_pose.click_turn_positive()
            if self.key_pressed("ArrowRight"):
                view_pose.click_turn_negative()
            if self.key_pressed("ArrowUp"):
                new_loc[0] += MOVEMENT_STEP_SZ * math.cos(view_pose.th)
                new_loc[1] += MOVEMENT_STEP_SZ * math.sin(view_pose.th)
                move_attempt = True
            if self.key_pressed("ArrowDown"):
                new_loc[0] -= MOVEMENT_STEP_SZ * math.cos(view_pose.th)
                new_loc[1] -= MOVEMENT_STEP_SZ * math.sin(view_pose.th)
                move_attempt = True
            if self.key_pressed("c"):
                new_loc[0] -= MOVEMENT_STEP_SZ * math.sin(view_pose.th)
                new_loc[1] += MOVEMENT_STEP_SZ * math.cos(view_pose.th)
                move_attempt = True
            if self.key_pressed("v"):
                new_loc[0] += MOVEMENT_STEP_SZ * math.sin(view_pose.th)
                new_loc[1] -= MOVEMENT_STEP_SZ * math.cos(view_pose.th)
                move_attempt = True
            if move_attempt:
                if height_bob_ampl < MAX_HEIGHT_BOB_AMPL:
                    height_bob_ampl += HEIGHT_BOB_VEL
                new_loc[0] = math_floor(new_loc[0] + 0.5)
                new_loc[1] = math_floor(new_loc[1] + 0.5)

                push_loop_iterations_per_frame(100)
                can_move = movement_ok([view_pose.x, view_pose.y], new_loc)
                pop_loop_iterations_per_frame()

                if can_move:
                    view_pose.x = new_loc[0]
                    view_pose.y = new_loc[1]
            else:
                height_bob_ampl -= 4.0 * HEIGHT_BOB_VEL
                if height_bob_ampl < 0.0:
                    height_bob_ampl = 0.0
            self.render()

    @pytch.when_key_pressed("d")
    def dump_pose(self):
        print(view_pose.x, view_pose.y, view_pose.th)


class Map(pytch.Sprite):
    Costumes = ["simplified-map.png"]

    @pytch.when_green_flag_clicked
    def setup(self):
        self.visible = False
        self.hide()
        self.set_size(MAP_SCALE_SIZE)

    @pytch.when_key_pressed("m")
    def toggle_map(self):
        self.visible = not self.visible
        if self.visible:
            self.show()
            self.go_to_front_layer()
        else:
            self.hide()


class MapMarker(pytch.Sprite):
    Costumes = ["map-marker.png"]

    @pytch.when_green_flag_clicked
    def run(self):
        self.enabled = False
        self.hide()
        self.set_size(0.5)
        while True:
            self.wait_seconds(0.5)
            if self.enabled:
                self.show()
            self.wait_seconds(0.5)
            self.hide()

    @pytch.when_I_receive("render")
    def mark_viewpose(self):
        map_x_01 = (view_pose.x - MAP_XMIN) / MAP_WD
        map_y_01 = (view_pose.y - MAP_YMIN) / MAP_HT

        stage_x = (map_x_01 - 0.5) * MAP_SCALED_IMG_WD
        stage_y = (map_y_01 - 0.5) * MAP_SCALED_IMG_HT
        self.go_to_xy(stage_x, stage_y)
        self.point_degrees(math.degrees(view_pose.th) - 45.0)

    @pytch.when_key_pressed("m")
    def toggle_map(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.hide()


class Frame(pytch.Sprite):
    Costumes = ["doom-frame.png"]

    @pytch.when_I_receive("render")
    def render(self):
        self.go_to_front_layer()


class TitlePic(pytch.Sprite):
    Costumes = [f"titlepic-post-{i:02d}.png" for i in range(30)]

    @pytch.when_green_flag_clicked
    def make_clones(self):
        for self.idx in range(30):
            self.create_clone()
        self.hide()

    @pytch.when_I_start_as_a_clone
    def init_clone(self):
        self.switch_costume(self.idx)
        self.set_x(-240 + 8 + self.idx * 16)

    @pytch.when_I_receive("play-intro")
    def slither_down(self):
        self.go_to_front_layer()
        self.wait_seconds(random.uniform(2.0, 4.0))
        self.glide_to_xy(self.x_position, -370, 2.0)

    @pytch.when_I_receive("run-game")
    def intro_over(self):
        self.delete_this_clone()


class WaitForIt(pytch.Sprite):
    Costumes = ["spinner.png"]

    @pytch.when_green_flag_clicked
    def run(self):
        self.keep_going = True
        while self.keep_going:
            self.turn_degrees(2)

    @pytch.when_I_receive("play-intro")
    def finish(self):
        self.keep_going = False
        self.hide()
