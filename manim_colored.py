from manim import *
from bitarray import bitarray
from bitarray.util import ba2int, int2ba
import seaborn as sb
import pandas as pd
from collections import deque

import platform
print(platform.platform())

def color_to_hex(color):
  return rgb_to_hex(color_to_rgb(color))

def hex_to_color(hex):
  return rgb_to_color(hex_to_rgb(hex))

import pprint
pp = pprint.PrettyPrinter(indent=2)


class CollatzSparseBits(Scene):

    def __init__(self, *args, **kwargs):
        super(CollatzSparseBits, self).__init__(*args, **kwargs)

        self.multibits = {}
        self.color_count = 1
        self.pallette = None
        self.display_group = VGroup()
        self.min_bit = 1
        self.max_bit = 1
        self.unit_width = 1
        self.buffer = 0 #0.1*self.unit_widt
        self.unit_height = 1
        self.scale_factor = 1


    def construct(self, seed: int):

        self.int_2_mobjects(seed)

        while len(self.multibits) > 1:

          #print(f'Ht: {config.frame_height}, Width: {config.frame_width}, Ratio: {config.aspect_ratio}')

          #self.calc_resize()

          #self.unit_height = self.multibits[self.min_bit][0].get_height()

          self.stretch_bits()

          self.add_double()

          self.add_one()

          self.collect()

          self.reduce_bit_height()


        self.wait(3)

    def reduce_bit_height(self):

        new_unit_height = self.multibits[self.min_bit][0].get_height()

        max_height = self.multibits[self.max_bit][0].get_height()

        if config.frame_height - max_height < 4:

          scale_factor /= 2

        self.play(*[group.animate.stretch_to_fit_height(group.get_height() - new_unit_height + 1.0)
                      for multistack in self.multibits.values() for group in multistack])

        self.play(*[colored_bit.animate.set_fill(colored_bit.get_color(), opacity=1.0) if int(group.get_height()) % 2 == 1
              else colored_bit.animate.set_fill(colored_bit.get_color(), opacity=0.0)
              for multistack in self.multibits.values() for group in multistack for colored_bit in group.submobjects])

        #self.play(self.display_group.animate.scale(resize_scale))
        self.multibits = {length - self.min_bit + 1: multi_stack  for length, multi_stack in self.multibits.items()}
        self.min_bit = 1

    def int_2_mobjects(self, seed):

        # convert to bits
        ba = int2ba(seed, endian="little")

        # get indices
        multibit_hts = [bit+1 for bit in ba.itersearch(1)]
        self.color_count = len(multibit_hts)
        self.max_bit = max(multibit_hts)

        self.pallette = sb.color_palette(n_colors=self.color_count)

        for i, length in enumerate(multibit_hts):
          bit_color = color.rgb_to_color(self.pallette[i])
          opacity = 1.0 if length % 2 == 1 else 0.0
          rectangle = Rectangle(width=self.unit_width,
                                height=length*self.unit_height,
                                color=bit_color)
          rectangle.set_fill(bit_color, opacity=opacity)
          multibit_group = VGroup(rectangle)
          self.multibits[length] = [multibit_group]
          self.display_group.add(multibit_group)


        self.display_group.arrange(direction=LEFT, buff=self.buffer)
        self.add(self.display_group.move_to(ORIGIN))

        '''
        {
          length = [
            [prev_red_portion, prev_green_portion, prev_blue_portion],
            [current_red_portion, current_green_portion, current_blue_portion],
            [carry_red_portion, carry_green_portion, carry_blue_portion]

          ]
        }

        {   #        OLD MULTIBIT  NEW MULTIBIT
          1: [array([1., 0., 0.]), array([1., 0., 0.])],
          3: [array([0.25, 0.75, 0.  ])],
          4: [array([0., 0., 1.])],
          5: [array([0., 0., 1.])]
        }

        '''


    def stretch_bits(self):

      self.play(*[multibit.animate.shift(LEFT*i*(self.unit_width+self.buffer))
                  for i, (multi_length, multi_stack) in enumerate(sorted(self.multibits.items(), reverse=False, key=lambda item: item[0])) for multibit in multi_stack], run_time=2)

      #self.play(*[multibit.animate.shift(LEFT*i*(self.unit_width+self.buffer)) for i, multi_stack in enumerate(self.multibits.values()) for multibit in multi_stack], run_time=2)
      self.play(self.display_group.animate.move_to(ORIGIN))


    def double_multibit(self, multibit_group, double_length):
      double_group = multibit_group.copy()
      old_height = multibit_group.get_height()
      new_height= old_height*double_length/(double_length-1)

      opacity = 1.0 if int(new_height) % 2 == 1 else 0.0
      double_group.stretch_to_fit_height(new_height)

      for colored_bit in double_group.submobjects:
          colored_bit.set_fill(colored_bit.get_color(), opacity=opacity)

      return double_group


    def add_double(self):

      copies = VGroup()
      doubles = VGroup()

      for ht, multi_stack in self.multibits.copy().items():

        double = ht + 1  # left shift
        copy = multi_stack[0].copy()
        copies.add(copy)

        double_copy = self.double_multibit(copy, double)
        doubles.add(double_copy)

        if double in self.multibits:
          self.multibits[double].append(double_copy)
        else:
          self.multibits[double] = [double_copy]

      self.play(*[ReplacementTransform(old, new) for old, new in zip(copies, doubles)])
      self.display_group.add(doubles)

      # Shift left
      self.play(*[double.animate.shift(LEFT*(self.unit_width+self.buffer))
                    for double in doubles],  run_time=2)

      self.play(self.display_group.animate.move_to(ORIGIN))


    def add_one(self):

      one_bits = self.multibits[self.min_bit]
      one_copy = one_bits[0].copy()
      one_bits.append(one_copy)

      self.add(one_copy)
      self.display_group.add(one_copy)
      #self.play(self.display_group.animate.move_to(ORIGIN))
      self.play(one_copy.animate.shift(RIGHT*(self.unit_width + self.buffer)))


    def build_tidbit_from_dict(self, tidbit_dict, old_length, old_height, buff=0.) -> VGroup:

      new_height = old_height*(old_length + 1)/old_length
      # color from hex
      opacity = 1.0 if int(new_height) % 2 == 1 else 0.0

      tidbit_group = VGroup(*[Rectangle(width=self.unit_width, height=pct_ht*new_height, color=hex_to_color(hex))
                      for hex, pct_ht in sorted(tidbit_dict.items(), reverse=True, key=lambda item: item[1])]).arrange(direction=UP, buff=buff)

      for colored_bit in tidbit_group.submobjects:
          colored_bit.set_fill(colored_bit.get_color(), opacity=opacity)

      return tidbit_group

    def mergeVGroups(self, l_group, r_group, multi_length):

      total_height = sum(obj.get_height() for obj in r_group.submobjects)

      l_tidbit = {color_to_hex(tidbit.get_color()): tidbit.get_height()/total_height for tidbit in l_group.submobjects}
      r_tidbit = {color_to_hex(tidbit.get_color()): tidbit.get_height()/total_height for tidbit in r_group.submobjects}

      # need to account for log scale - mean of pct length
      mean = dict(pd.DataFrame([l_tidbit, r_tidbit]).fillna(0).mean())

      merged_group = self.build_tidbit_from_dict(mean, multi_length, total_height)

      merged_group.set_y(0).set_x(r_group.get_x())

      return merged_group


    def create_stack_group(self, stack):
       return VGroup(*[group for multilength in stack for group in self.multibits[multilength]])

    def create_display_group(self):
       return VGroup(*[group for multistack in self.multibits.values() for group in multistack])


    def merge(self, multi_length, stack):

      multibit_list = self.multibits.get(multi_length, [])
      carries = len(multibit_list)

      if carries > 1:

          double = multi_length + 1

          multibit1 = multibit_list[0]

          multibit2 = multibit_list[1]

          merge_source_group = VGroup(multibit1, multibit2)

          merge_target_group = self.mergeVGroups(multibit1, multibit2, multi_length)

          #self.stack_group.add(merge_target_group)

          stack_group = self.create_stack_group(stack)

          if double in self.multibits:
            self.multibits[double].append(merge_target_group)
          else:
            self.multibits[double] = [merge_target_group]
            stack.append(double)


          if carries > 2:
            self.multibits[multi_length] = [multibit_list[2]]
          else:
            del self.multibits[multi_length]

          self.play(ReplacementTransform(merge_source_group, merge_target_group),
                    stack_group.animate.shift(RIGHT*(self.unit_width + self.buffer)), run_time=2)
          self.wait(1)


    def collect(self, method='firstTwo'):

      assert self.multibits, 'cannot perform collect method without seed multibits'

      stack = deque(sorted(self.multibits.keys(), reverse=True))
      #self.stack_group = VGroup(*[group for multistack in self.multibits.values() for group in multistack])



      while stack:
        multi_length = stack.pop()
        #self.stack_group.remove(*[multibit for multibit in self.multibits[multi_length]])
        self.merge(multi_length, stack)


      self.min_bit = min(self.multibits.keys())
      self.max_bit = max(self.multibits.keys())
      self.display_group = self.create_display_group()
      self.play(self.display_group.animate.move_to(ORIGIN))


