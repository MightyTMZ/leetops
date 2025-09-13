from django.contrib import admin
from .models import *

admin.site.register(Company)
admin.site.register(SimulationSession)
admin.site.register(Simulation)
admin.site.register(IncidentAttempt)
admin.site.register(Incident)
admin.site.register(Rating)
admin.site.register(UserRating)
admin.site.register(CompletedSimulation)