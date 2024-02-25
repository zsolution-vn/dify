from blinker import signal

# sender: model invoke
model_was_invoked = signal('model-was-invoked')
