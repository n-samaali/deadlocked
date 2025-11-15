import description
import generator

class Game:
    def __init__(self):
        pass
        # self.key = key 
        # self.options = options
    
    def draw_card(self):
        event = description.pioche()
        return event
    
    def start(self):
        event = ""
        a = generator.call_ai(event, prompt="")
        print(a)
        self.options = generator.parse_options(a)
        print(self.options)
        
    def next_turn(self):
        event = self.draw_card()
        print(event[1])#the ascii card
        a = generator.call_ai(event[0], self.options['Strength'])
        print(a)
        self.options = generator.parse_options(a)
        print(self.options)