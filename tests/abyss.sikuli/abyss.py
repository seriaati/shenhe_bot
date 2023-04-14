def wait_and_click(image):
    wait(image)
    click(image)

def type_command():
    type(Key.ESC)
    type("/abyss")
    wait("1681431503714.png")
    type(Key.ENTER)


# test general abyss command
type_command()
wait("1681431521194.png")
type(Key.ENTER)

# test with last phase
def test_last_phase():
    type_command()
    type(Key.DOWN)
    type(Key.ENTER)
    type(Key.DOWN)
    type(Key.ENTER)
test_last_phase()
type(Key.ENTER)

# test with last phase and another user
test_last_phase()
type(Key.DOWN)
type(Key.ENTER)
type("galvin")
type(Key.ENTER)
type(Key.ENTER)

waitVanish("1681432219503.png")

# test floor image generation
def click_dropdown():
    wait_and_click("1681431880986.png")
    wait(0.3)
    
click_dropdown()
type(Key.DOWN)
type(Key.ENTER)

# test one-image generation
click_dropdown()
for i in range(5):
    type(Key.DOWN)
type(Key.ENTER)