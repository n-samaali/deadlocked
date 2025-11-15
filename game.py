import description
import generator
import Person

class Game:
    def __init__(self):
        pass
        # self.key = key 
        # self.options = options
        self.person = Person.Person()
    
    def draw_card(self):
        event = description.pioche()
        return event
    
    def card_verificator(self, event):
        key = event.split(":")[0]
        if key=="QH":
            self.person.game_over()
            
    def start(self):
        event = ""
        a = generator.call_ai(event, prompt="")
        print(a)
        self.options = generator.parse_options(a)
        print(self.options)
        
    def next_turn(self):
        event = self.draw_card()
        print(event[1])#the ascii card
        self.card_verificator(event[0])
        a = generator.call_ai(event[0], self.options['Charisma'])
        print(a)
        hp_stuff = generator.extract_modifier(a)
        
        if hp_stuff[0] is not None:
            action, value = hp_stuff

            if action == "Reduce":
                self.person.reduce_hp(value)

            elif action == "Increase":
                self.person.increase_hp(value)

            print("Current HP:", self.person.hp)
    
        self.options = generator.parse_options(a)
        print(self.options)