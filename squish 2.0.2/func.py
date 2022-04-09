import pygame, os, time

class game():
    def __init__(self):
        pygame.init()
        self.running = 1

        pygame.display.set_caption('squish')
        self.display_info = pygame.display.Info()
        self.display_size = [self.display_info.current_w, self.display_info.current_h]
        self.display = pygame.display.set_mode(self.display_size)
        self.surface = pygame.Surface(self.display_size)
        self.clock = pygame.time.Clock()
        self.tick = 60

        self.reset_joysticks()

        cwd = os.getcwd()
        pgd = os.path.join(cwd, 'pages')
        self.pages = {}
        for pg in os.listdir(pgd):
            file = open(os.path.join(pgd, pg), encoding = 'utf-8')
            self.pages[pg.replace('.txt', '')] = page(file.readlines(), self.display_size)
            file.close()

        self.page = 'main'
        self.next_page = 'main'
        self.reset_menu_navigation()

        self.players = []

        self.valid_name_inputs = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789'
        self.valid_hex_inputs = '0123456789abcdefABCDEF'
        self.valid_inputs = ''
        self.text_input = ''
        self.text_last_input = ''
        self.text_input_action = -1

    def reset_menu_navigation(self):
        # Page variables
        self.cursor = [0, 0]
        self.mouse_rmb = 0
        self.mouse_wheel = 0
        self.scroll_speed = 15
        self.menu_controls = {'up': 0,
                              'down': 0,
                              'left': 0,
                              'right': 0,
                              'select': 0,
                              'back': 0,
                              'page_entrance': 0}
        self.menu_input_delay_index = [0, 0]
        self.menu_input_timedelay_first = 0.5
        self.menu_input_timedelay_second = 0.1
        self.menu_input_timestamp = [time.time() - self.menu_input_timedelay_first, time.time() - self.menu_input_timedelay_first]

    def reset_joysticks(self):
        self.joystick_threshold = 0.5
        self.joysticks = []
        self.controllers = []
        for i in range(0, pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(i))
            self.joysticks[i].init()
            self.controllers.append(controller(self.joysticks[i], self.joystick_threshold))
    
    def get_inputs(self):
        self.mouse_moved = not ((0,0) == pygame.mouse.get_rel())
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_last_rmb = self.mouse_rmb
        self.mouse_rmb = pygame.mouse.get_pressed()[0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = 0
            if event.type == pygame.MOUSEWHEEL:
                self.mouse_wheel = -1 * event.y * self.scroll_speed
            if (event.type == pygame.KEYDOWN) or (event.type == pygame.KEYUP):
                key_direction = (event.type == pygame.KEYDOWN)
                if event.key == pygame.K_UP:
                    self.menu_controls['up'] = key_direction
                    self.menu_input_delay_index[1] = 0
                elif event.key == pygame.K_DOWN:
                    self.menu_controls['down'] = key_direction
                    self.menu_input_delay_index[1] = 0
                elif event.key == pygame.K_LEFT:
                    self.menu_controls['left'] = key_direction
                    self.menu_input_delay_index[0] = 0
                elif event.key == pygame.K_RIGHT:
                    self.menu_controls['right'] = key_direction
                    self.menu_input_delay_index[0] = 0
                elif event.key == pygame.K_RETURN:
                    self.menu_controls['select'] = key_direction
                elif event.key == pygame.K_ESCAPE:
                    self.menu_controls['back'] = key_direction
                if key_direction and (self.text_input_action != -1):
                    if event.key == pygame.K_BACKSPACE:
                        self.text_input = self.text_input[:-1]
                    elif (self.text_input_limit == -1) or (len(self.text_input) < self.text_input_limit):
                        if self.valid_inputs.count(event.unicode):
                            self.text_input += event.unicode
                    self.apply_text_input(self.text_input)
        #print(pygame.key.start_text_input())
        for kontroller in self.controllers:
            kontroller.check_inputs(self.menu_controls, self.menu_input_delay_index)

    def run_page(self):
        for control in self.pages[self.page].controls:
            if control.trigger == 'page_entrance':
                if self.menu_controls[control.trigger]:
                    self.do_action(control.action)

        for block in self.pages[self.page].blocks:
            if block.color != -1:
                pygame.draw.rect(self.surface, block.color, [block.pos, block.size])
            if block.text_image != 0:
                self.surface.blit(block.text_image, block.text_pos)
        
        do_menu_navigation = [0, 0]
        if self.text_input_action == -1:
            for i in range(0, 2):
                if self.menu_input_delay_index[i] == 0:
                    do_menu_navigation[i] = 1
                    self.menu_input_delay_index[i] = 1
                    self.menu_input_timestamp[i] = time.time()
                elif self.menu_input_delay_index[i] == 1:
                    if self.menu_input_timestamp[i] + self.menu_input_timedelay_first <= time.time():
                        do_menu_navigation[i] = 1
                        self.menu_input_delay_index[i] = 2
                        self.menu_input_timestamp[i] = time.time()
                elif self.menu_input_delay_index[i] == 2:
                    if self.menu_input_timestamp[i] + self.menu_input_timedelay_second <= time.time():
                        do_menu_navigation[i] = 1
                        self.menu_input_timestamp[i] = time.time()

            for button in self.pages[self.page].buttons:
                if in_rect(self.mouse_pos, button.pos, button.size):
                    if self.mouse_moved:
                        do_menu_navigation = [0, 0]
                        self.cursor = [button.button_pos[0], button.button_pos[1]]
                    elif self.mouse_rmb and not self.mouse_last_rmb:
                        do_menu_navigation = [0, 0]
                        self.cursor = [button.button_pos[0], button.button_pos[1]]
                        self.menu_controls['select'] = 1
            
            if do_menu_navigation[0]:
                if self.menu_controls['left']:
                    while 1:
                        self.cursor[0] = (self.cursor[0] - 1) % len(self.pages[self.page].button_array)
                        if self.pages[self.page].button_array[self.cursor[0]][self.cursor[1]] != 1:
                            for i in range(0, len(self.pages[self.page].button_array)):
                                if self.pages[self.page].button_array[self.cursor[0]][i] == 1:
                                    self.cursor[1] = i
                                    break
                            else:
                                continue
                            break
                        else:
                            break
                if self.menu_controls['right']:
                    while 1:
                        self.cursor[0] = (self.cursor[0] + 1) % len(self.pages[self.page].button_array)
                        if self.pages[self.page].button_array[self.cursor[0]][self.cursor[1]] != 1:
                            for i in range(0, len(self.pages[self.page].button_array)):
                                if self.pages[self.page].button_array[self.cursor[0]][i] == 1:
                                    self.cursor[1] = i
                                    break
                            else:
                                continue
                            break
                        else:
                            break
            if do_menu_navigation[1]:
                if self.menu_controls['up']:
                    while 1:
                        self.cursor[1] = (self.cursor[1] - 1) % len(self.pages[self.page].button_array)
                        if self.pages[self.page].button_array[self.cursor[0]][self.cursor[1]] != 1:
                            for i in range(0, len(self.pages[self.page].button_array)):
                                if self.pages[self.page].button_array[i][self.cursor[1]] == 1:
                                    self.cursor[0] = i
                                    break
                            else:
                                continue
                            break
                        else:
                            break
                if self.menu_controls['down']:
                    while 1:
                        self.cursor[1] = (self.cursor[1] + 1) % len(self.pages[self.page].button_array)
                        if self.pages[self.page].button_array[self.cursor[0]][self.cursor[1]] != 1:
                            for i in range(0, len(self.pages[self.page].button_array)):
                                if self.pages[self.page].button_array[i][self.cursor[1]] == 1:
                                    self.cursor[0] = i
                                    break
                            else:
                                continue
                            break
                        else:
                            break

        else:
            if self.menu_controls['select'] or (self.mouse_rmb and not self.mouse_last_rmb):
                self.menu_controls['select'] = 0
                self.text_input_action = -1
            elif self.menu_controls['back']:
                self.apply_text_input(self.text_last_input)
                self.text_input_action = -1
                self.menu_controls['back'] = 0

        
        for button in self.pages[self.page].buttons:
            if self.cursor == button.button_pos:
                if self.menu_controls['select']:
                    self.menu_controls['select'] = 0
                    self.do_action(button.action)
                if self.text_input_action == button.action:
                    pygame.draw.rect(self.surface, button.text_active_color, [button.pos, button.size])
                else:
                    pygame.draw.rect(self.surface, button.active_color, [button.pos, button.size])
            elif button.color != -1:
                pygame.draw.rect(self.surface, button.color, [button.pos, button.size])
            if button.text_image != 0:
                if button.action[0] == 'input':
                    if button.action[1] == 'player':
                        if button.action[2] == 'name':
                            button.text_input = self.players[-1].name
                        elif button.action[2] == 'base_color':
                            if self.text_input_action == button.action:
                                button.text_input = '0x' + self.text_input
                            else:
                                button.text_input = '{0:#0{1}x}'.format(self.players[-1].base_color, 8)
                    self.surface.blit(text2img(button.text + button.text_input, button.text_color, button.text_font, button.text_size, button.text_bold)[0], button.text_pos)
                else:
                    self.surface.blit(button.text_image, button.text_pos)

        for player_list in self.pages[self.page].player_lists:
            if self.mouse_wheel and not player_list.only_last_player:
                player_list.scroll(self.mouse_wheel, len(self.players))
            list_surface = pygame.Surface(player_list.size)
            list_surface.fill(player_list.color)
            for i in range((player_list.only_last_player) * (len(self.players) - 1), len(self.players)):
                player = self.players[i]
                if player_list.only_last_player:
                    i = 0
                entry_surface = pygame.Surface(player_list.entry_size)
                if player_list.color != -1:
                    entry_surface.fill(player_list.entry_color)
                pygame.draw.rect(entry_surface, player.base_color, [player_list.player_pos, player_list.player_size])
                entry_surface.blit(text2img(player.name, player_list.text_color, player_list.text_font, player_list.text_size, player_list.text_bold)[0], player_list.text_pos)
                list_surface.blit(entry_surface, [0, i * (player_list.entry_size[1] + player_list.entry_spacing) - player_list.scroll_value])
            self.surface.blit(list_surface, player_list.pos)

        for control in self.pages[self.page].controls:
            if control.trigger != 'page_entrance':
                if self.menu_controls[control.trigger]:
                    self.do_action(control.action)
     
    def do_action(self, action):
        if action[0] == 'quit':
            self.running = 0
        elif action[0] == 'goto':
            self.reset_menu_navigation()
            self.next_page = action[1]
        elif action[0] == 'update_controllers':
            self.reset_joysticks()
        elif action[0] == 'new':
            if action[1] == 'player':
                self.players.append(player(len(self.players) + 1))
        elif action[0] == 'set':
            if action[1] == 'player':
                if action[2] == 'base_color':
                    self.players[-1].base_color = int(action[3], 16)
        elif action[0] == 'input':
            if action[1] == 'player':
                if action[2] == 'name':
                    self.text_input = self.players[-1].name
                    self.text_last_input = self.text_input
                    self.text_input_action = action
                    self.valid_inputs = self.valid_name_inputs
                if action[2] == 'base_color':
                    self.text_input = hex(self.players[-1].base_color)[2:]
                    self.text_last_input = self.text_input
                    self.text_input_action = action
                    self.valid_inputs = self.valid_hex_inputs
                if len(action) <= 3:
                    self.text_input_limit = -1
                else:
                    self.text_input_limit = int(action[3])
        elif action[0] == 'remove':
            if action[1] == 'player':
                if len(self.players) > 0:
                    self.players.pop()

    def apply_text_input(self, text):
        if self.text_input_action != -1:
            if self.text_input_action[1] == 'player':
                if self.text_input_action[2] == 'name':
                    self.players[-1].name = text
                if self.text_input_action[2] == 'base_color':
                    if text:
                        self.players[-1].base_color = int(text.ljust(6, '0'), 16)
                    else:
                        self.players[-1].base_color = 0xbbbbbb
    
    def update(self):
        self.display.blit(pygame.transform.scale(self.surface, self.display_size), [0, 0])
        pygame.display.update()
        self.clock.tick(self.tick)
        self.menu_controls['page_entrance'] = (self.page != self.next_page)
        self.page = self.next_page
    
    def close(self):
        pygame.quit()

class page():
    def __init__(self, file, display_size):
        self.blocks = []
        self.buttons = []
        self.controls = []
        self.player_lists = []
        objekt_type = 0
        objekt = 0
        for line in file:
            no_spaces_line = line.replace(' ', '')
            no_return_line = no_spaces_line.replace('\n', '')
            split_line = no_return_line.split('=')
            property = split_line[0]
            value = split_line[-1]
            if property == 'block':
                if objekt != 0:
                    self.append_objekt(objekt, objekt_type)
                objekt_type = 'block'
                objekt = menu_block()
            elif property == 'button':
                if objekt != 0:
                    self.append_objekt(objekt, objekt_type)
                objekt_type = 'button'
                objekt = menu_button()
            elif property == 'control':
                if objekt != 0:
                    self.append_objekt(objekt, objekt_type)
                objekt_type = 'control'
                objekt = menu_control()
            elif property == 'player_list':
                if objekt != 0:
                    self.append_objekt(objekt, objekt_type)
                objekt_type = 'player_list'
                objekt = menu_player_list()
            elif property == 'button_pos':
                xy = findxy(no_return_line)
                objekt.button_pos = [int(xy[0]), int(xy[1])]
            elif property == 'size':
                objekt.size = findxy(no_return_line, display_size)
            elif property == 'pos':
                objekt.pos = findxy(no_return_line, display_size, [0, 0], objekt.size)
            elif property == 'color':
                objekt.color = int(value, 16)
            elif property == 'entry_size':
                objekt.entry_size = findxy(no_return_line, display_size)
            elif property == 'entry_spacing':
                objekt.entry_spacing = findx(value, objekt.size[1])
            elif property == 'entry_color':
                objekt.entry_color = int(value, 16)
            elif property == 'player_size':
                objekt.player_size = findxy(value, objekt.entry_size)
            elif property == 'player_pos':
                objekt.player_pos = findxy(value, objekt.entry_size, [0, 0], objekt.player_size)
            elif property == 'only_last_player':
                objekt.only_last_player = int(value)
            elif property == 'active_color':
                objekt.active_color = int(value, 16)
            elif property == 'text_active_color':
                objekt.text_active_color = int(value, 16)
            elif property == 'text':
                objekt.text = line.split("'")[1]
            elif property == 'text_color':
                objekt.text_color = (int(value[2:4], 16), int(value[4:6], 16), int(value[6:8], 16))
            elif property == 'text_bold':
                objekt.text_bold = (value.lower() == 'true') or (value == '1')
            elif property == 'text_font':
                objekt.text_font = value
            elif property == 'text_size':
                objekt.text_size = int(value)
                [objekt.text_image, objekt.text_image_size] = text2img(objekt.text, objekt.text_color, objekt.text_font, objekt.text_size, objekt.text_bold)
            elif property == 'text_pos':
                if objekt_type == 'player_list':
                    objekt.text_pos = findxy(no_return_line, objekt.entry_size, [0, 0], objekt.text_image_size)
                else:
                    objekt.text_pos = findxy(no_return_line, objekt.size, objekt.pos, objekt.text_image_size)
            elif property == 'text_input_limit':
                objekt.text_input_limi = int(value)
            elif property == 'trigger':
                objekt.trigger = value
            elif property == 'action':
                objekt.action = value.split(':')
            elif property == 'value':
                objekt.value = value
        self.append_objekt(objekt, objekt_type)
        self.button_array = [[0]]
        for button in self.buttons:
            for i in range(len(self.button_array), max(button.button_pos) + 1):
                self.button_array.append([0])
                for ii in range(0, len(self.button_array[0])):
                    self.button_array[ii].append(0)
                    self.button_array[-1].append(0)
            self.button_array[button.button_pos[0]][button.button_pos[1]] = 1
    
    def append_objekt(self, objekt, objekt_type):
        if objekt_type == 'block':
            self.blocks.append(objekt)
        elif objekt_type == 'button':
            self.buttons.append(objekt)
        elif objekt_type == 'control':
            self.controls.append(objekt)
        elif objekt_type == 'player_list':
            self.player_lists.append(objekt)

class menu_block():
    def __init__(self):
        self.size = [0, 0]
        self.pos = [0, 0]
        self.color = -1
        self.text = ''
        self.text_color = 0x000000
        self.text_bold = 0
        self.text_font = 'couriernew'
        self.text_size = 1
        self.text_image = 0
        self.text_image_size = [0, 0]
        self.text_pos = [0, 0]

class menu_button():
    def __init__(self):
        self.button_pos = [0, 0]
        self.size = [0, 0]
        self.pos = [0, 0]
        self.color = -1
        self.active_color = -1
        self.text_active_color = -1
        self.text = ''
        self.text_input = ''
        self.text_color = 0x000000
        self.text_bold = 0
        self.text_font = 'couriernew'
        self.text_size = 1
        self.text_image = 0
        self.text_image_size = [0, 0]
        self.text_pos = [0, 0]
        self.text_input_limit = -1
        self.action = [-1]
        self.value = 0

class menu_control():
    def __init__(self):
        self.trigger = 0
        self.action = [-1]

class menu_player_list():
    def __init__(self):
        self.size = [0, 0]
        self.pos = [0, 0]
        self.color = -1
        self.entry_size = [0, 0]
        self.entry_spacing = 0
        self.entry_color = -1
        self.player_size = [0, 0]
        self.player_pos = [0, 0]
        self.only_last_player = 0
        self.text = ''
        self.text_color = 0x000000
        self.text_bold = 0
        self.text_font = 'couriernew'
        self.text_size = 1
        self.text_pos = [0, 0]
        self.scroll_value = 0
    
    def scroll(self, scroll_distance, player_count):
        self.scroll_value += scroll_distance
        scroll_limit = player_count * self.entry_size[1] + (player_count - 1) * self.entry_spacing - self.size[1]
        if self.scroll_value > scroll_limit:
            self.scroll_value = scroll_limit
        if self.scroll_value < 0:
            self.scroll_value = 0

class controller():
    def __init__(self, joystick, joystick_threshold):
        self.joystick = joystick
        self.joystick_threshold = joystick_threshold
        self.controls = {'up': [0, 0, -1, pygame.CONTROLLER_AXIS_LEFTY, pygame.CONTROLLER_BUTTON_DPAD_UP],
                         'down': [0, 0, 1, pygame.CONTROLLER_AXIS_LEFTY, pygame.CONTROLLER_BUTTON_DPAD_DOWN],
                         'left': [0, 0, -1, pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_BUTTON_DPAD_LEFT],
                         'right': [0, 0, 1, pygame.CONTROLLER_AXIS_LEFTX, pygame.CONTROLLER_BUTTON_DPAD_RIGHT],
                         'jump': [0, 0, -1, pygame.CONTROLLER_AXIS_LEFTY, pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_B],
                         'shield': [0, 0, 2, pygame.CONTROLLER_AXIS_TRIGGERRIGHT, pygame.CONTROLLER_AXIS_TRIGGERLEFT, pygame.CONTROLLER_BUTTON_RIGHTSHOULDER, pygame.CONTROLLER_BUTTON_LEFTSHOULDER],
                         'select': [0, 0, 0, pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_START],
                         'back': [0, 0, 0, pygame.CONTROLLER_BUTTON_B, pygame.CONTROLLER_BUTTON_BACK]}

    def check_inputs(self, menu_controls, menu_input_delay_index):
        for control in self.controls:
            self.controls[control][1] = self.controls[control][0]
            self.controls[control][0] = 0
            for i in range(3, len(self.controls[control])):
                if abs(self.controls[control][2]) > i - 3:
                    if ((1 - 3 * (self.controls[control][2] < 0)) * self.joystick.get_axis(self.controls[control][i]) > self.joystick_threshold):
                        self.controls[control][0] = 1
                        break
                elif self.joystick.get_button(self.controls[control][i]):
                    self.controls[control][0] = 1
                    break
            if self.controls[control][0] ^ self.controls[control][1]:
                menu_controls[control] = self.controls[control][0]
                if (control == 'up') or (control == 'down'):
                    menu_input_delay_index[1] = 0
                elif (control == 'left') or (control == 'right'):
                    menu_input_delay_index[0] = 0

class player():
    def __init__(self, player_number):
        self.name = 'Player ' + str(player_number)
        self.base_color = 0xbbbbbb
        self.color = -1
        self.size = [0, 0]
        self.alive = 0
        
        self.position = [0, 0]
        self.desired_position = [0, 0]
        self.base_speed = [0, 0]
        self.speed = [0, 0]
        self.desired_speed = [0, 0]
        self.acceleration = 0
        self.gravity = 0
        self.jump_strength = 0
        
        self.score = 0

def text2img(text, color, font, font_size, is_bold):
    font = pygame.font.SysFont(font, font_size, is_bold)
    rendered_text = font.render(text, False, color)
    text_size = font.size(text)
    return rendered_text, text_size

def in_rect(point, rect_pos, rect_size):
    for i in range(0, len(point)):
        if point[i] < rect_pos[i] or point[i] > rect_pos[i] + rect_size[i]:
            return 0
    return 1

def findxy(string, refrence_size = [0, 0], refrence_pos = [0, 0], self_size = [0, 0]):
    # Find [x, y] in 'word = [jxx, jxy]'
    # j = r,d: right/down justified
    # j = l,u: left/up justified
    # j = c: centered justified
    # 'x' means relative to refrence
    string = string.split('[')[-1]
    string = string.split(']')[0]
    string = string.split(',')
    xy = [0, 0]
    match = -1
    for i in range(0, 2):
        if (string[i][0] == 'l') or (string[i][0] == 'u'):
            if (string[i][1] == 'x'):
                xy[i] = refrence_pos[i] + refrence_size[i] * float(string[i][2:])
            else:
                xy[i] = float(string[i][1:])
        elif string[i][0] == 'c':
            if (string[i][1] == 'x'):
                xy[i] = refrence_pos[i] + refrence_size[i] * float(string[i][2:]) - 0.5 * self_size[i]
            else:
                xy[i] = float(string[i][1:]) - 0.5 * self_size[i]
        elif (string[i][0] == 'r') or (string[i][0] == 'd'):
            if (string[i][1] == 'x'):
                xy[i] = refrence_pos[i] + refrence_size[i] * float(string[i][2:]) - self_size[i]
            else:
                xy[i] = float(string[i][1:]) - self_size[i]
        elif string[i][0] == 'x':
            xy[i] = refrence_size[i] * float(string[i][1:])
        elif string[i][0] == 'm':
            match = i
        else:
            xy[i] = float(string[i])
    if match != -1:
        xy[match] = xy[not match]
    return xy

def findx(string, refrence_size = 0):
    # Find x 'word = xx'
    # 'x' means relative to refrence
    if string[0] == 'x':
        return refrence_size * float(string[1:])
    return float(string)