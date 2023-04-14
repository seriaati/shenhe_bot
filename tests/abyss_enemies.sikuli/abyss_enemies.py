# type: ignore

type(Key.ESC)
type("/abyss-enemies")
wait("1681432525636.png")
type(Key.ENTER)
type(Key.ENTER)
wait("1681432564330.png")

# test blessin
click("1681432577960.png")
wait(1.0)

# test floors
def wait_vanish():
    waitVanish("Snipaste_2023-04-14_08-37-05.png")
    wait(1.0)

images = ["1681432590331.png", "1681432689366.png", "1681432701608.png"]
for image in images:
    click(image)
    wait_vanish()