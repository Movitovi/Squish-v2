import func
game = func.game()
while game.running:
    game.get_inputs()
    game.run_page()
    game.update()
game.close()