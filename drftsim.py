#!/usr/bin/python
from random import randint

# user inputs
membership_nights_per_mo = 2
num_agents = 10
rooms_backed_per_agent = 1.5

# % of time members are traveling IN network, on average.
member_percent_time_travel = .50

room_price_min = 40.0
room_price_max = 200.0

# calculated
globavg_room_price = 0
globavg_occupancy = .60

# check - global occupancy can't be less than member travel time
if member_percent_time_travel > globavg_occupancy:
	raise Exception, "globavg occupancy cannot be lower than % of time members are traveling in network"

class Agent(object):
	def __init__(self, drft_bal = 0, dollar_bal = 0, room_price = 0):
		self.id = id(self)
		self.drft_bal = drft_bal
		self.dollar_bal = dollar_bal
		self.room_price = room_price
		self.room_nights_contributed = 0
		self.room_nights_used = 0

agents = []

# initialize the agents
sum_room_prices = 0
for i in range(0,num_agents):
	a = Agent()
	a.room_price = randint(room_price_min, room_price_max)
	sum_room_prices += a.room_price
	a.drft_bal = membership_nights_per_mo
	agents.append(a)

print 'agents initialized. example:'
print '    drft_bal', agents[0].drft_bal
print '    dollar_bal', agents[0].dollar_bal
print '    room_price', agents[0].room_price

# simplified model that assumes no constraint on room supply - ie, for example,
# that each agent is backing an extra room or bed somewhere. 

# calculate globavg_room_price
globavg_room_price = sum_room_prices/float(len(agents))

# start at time 1 only because we already credited the agents with their t=0
# membership credits
t = 1 
# run for 100 days
while t <= 100:
	# generate single-night reservations for percent_time_travel number of rooms (agents)
	#	(ensure no room collisions)
	#   randomly select traveling agent ta
	#   randomly select host agent ha
	num_member_travelers = member_percent_time_travel*num_agents
	print 'generating reservations for %d member travelers (there may be rounding)\n' % int(round(num_member_travelers))

	# save a list of available agents so there's no collisions
	available_travelers = range(len(agents))
	available_hosts = range(len(agents))
	guest_income = 0
	# remember who was a host this period
	hosts_this_period = []
	traveler_members_this_period = []

	for i in range(0,int(round(num_member_travelers))):
		# randomly select traveling agent from the remaining ones available
		ta_idx = randint(0, len(available_travelers)-1)
		idx = available_travelers.pop(ta_idx)
		ta = agents[idx]
		ta.room_nights_used += 1

		# a 'ta' cannot travel twice, but an 'ha' can host twice. and in
		# general they can also host themselves (ie, 'staying at home').  so we
		# randomly select an 'ha' from an independent and non-subtractive list. 
		ha_idx = randint(0, len(available_hosts)-1)
		ha = agents[ha_idx]

		# for each member res:
		#	  increase host drft_bal
		#	  subtract member drft_bal
		if ta.drft_bal == 0:
			ta.dollar_bal -= ha.room_price
			guest_income += ha.room_price
		else:
			ta.drft_bal -= 1

		ha.drft_bal += 1

		print 'agent %d stayed with agent %d.' % (ta.id, ha.id)
		print 'traveler balance: %d. host balance: %d\n' % (ta.drft_bal, ha.drft_bal) 

		if ta in traveler_members_this_period:
			raise Exception, "Error: a member cannot travel in two places at once. idx = %d, ta.id = %d" % (idx, ta.id)
		else:
			traveler_members_this_period.append(ta)

		if ta.drft_bal < 0:
			raise Exception, "Error, agent %d drft balance is %d" % (ta.id, ta.drft_bal)

		hosts_this_period.append(ha)

	# generate single-night reservations for (globavg_occupancy - member_percent_time_travel)%
	percent_guests = globavg_occupancy - member_percent_time_travel
	num_guest_travelers = percent_guests*num_agents
	print 'generating reservations for %d guest travelers (there may be rounding)\n' % int(round(num_guest_travelers))
	for i in range(0, int(round(num_guest_travelers))):
		#   randomly select hosting agent ha
		#   with paying guests, there is no traveling agent who spends credits
		ha_idx = randint(0, len(available_hosts)-1)
		ha = agents[ha_idx]
		#   for each member res:
		#	  increase host drft_bal
		#	  update dollar_bal (or store centrally so we can average it and distribute in a sec)
		ha.drft_bal += 1
		hosts_this_period.append(ha)
		guest_income += ha.room_price
		print 'a guest stayed with agent %d for %f.' % (ha.id, ha.room_price)

	print 'sanity check for t=%d' % t
	print '    num guests = %d' % num_guest_travelers
	print '    num traveling members = %d' % num_member_travelers
	print '    hosts this period %d' % len(hosts_this_period)
	print '    percent global occupancy = %f' % (globavg_occupancy)
	print '    total rooms (should be same as hosts): %f\n' % (globavg_occupancy*len(agents))

	# *** update globavg_occupancy?
	# right now we can leave it fixed - later we can make it vary between a min
	# and max value. 

	# calculate proportionate distribution of guest income to all agents
	#   sum all host nights 
	#   sum of all reservation dollar values
	#   divide sum reservation dollar values/agent with reservations
	#   add this weighted average to the dollar_bal of each agent that had a reservation that night. 
	#   note that in general a single host might be in this list multiple
	#   times, and will receive the appropriate number of shares
	#   commensurately. 
	num_ha = len(hosts_this_period)
	averaged_guest_share = float(guest_income)/num_ha
	for ha in hosts_this_period:
		ha.dollar_bal += averaged_guest_share
		print 'agent %d earned %f' % (ha.id, averaged_guest_share)

	# true up for average occupancy?

	#if t modulo 30, each agent buys another round of membership_nights 
	if t%30 == 0:
		for a in agents:
			a.drft_bal += membership_nights_per_mo
			a.dollar_bal -= globavg_room_price*membership_nights_per_mo
		print "all members purchased %d DRFT at a rate of %f." % (membership_nights_per_mo, globavg_room_price)

	print "\nagent_id, drft_bal, dollar_bal, room_nights_contributed, room_nights_used"
	total_drft = 0
	total_dollars = 0
	for a in agents:
		a.room_nights_contributed += rooms_backed_per_agent
		total_drft += a.drft_bal
		total_dollars += a.dollar_bal
		print a.id, a.drft_bal, a.dollar_bal, a.room_nights_contributed, a.room_nights_used

	print "total DRFT: ", total_drft
	print "total dollars in system: ", total_dollars
	# increment time 
	t += 1
	raw_input("press enter to continue...\n\n")

'''
# todo
* DONE add in income calcuation for monthly membership nights. 
* actually model lost nights, not just gained nights. (this model essentially assumes each agent backs at least one extra room - though we do need to constrain number of guests at once then!)
  * still to be done:***
  * available_hosts needs to be multiplied by the number of rooms each user is backing
  * then the available_hosts list DOES need to be subtractive
* track how many times a user paid $ for their stay, and average price/night compared to list guest price.
* introduce variability in occupancy night by night, w average occupancy being what's given
* let a user specify their own travel frequency and guest room price as input. 
* true up for average occupancy?
'''
