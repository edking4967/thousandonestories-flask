from wtforms import Form, BooleanField, TextField, PasswordField, validators

class WriteForm(Form):
    text = TextField('Story', [validators.Length(min=100,max=10000)] )
    title = TextField('Title', [validators.Length(min=1,max=500)]  )
