import os,sys,time
import obsws_python

OBS_SCENE_NAME = '场景'
STICKER_ITEM_NAME = '图像'
TEXT_ITEM_NAME = '数据'

global zero_gold_alert

global obs_client
try:
	obs_client = obsws_python.ReqClient(host='localhost', port=4455)
except:
	obs_client = None
	print("Obs websocket connect error.")

def post_result(data, isblackout):
	global zero_gold_alert
	zero_gold_alert = False
	output = ""
	if "vsHistoryDetail" in data["data"]:
		output = get_battle_msg(data, isblackout)
	elif "coopHistoryDetail" in data["data"]:
		output = get_coop_msg(data, isblackout)
	else: 
		return
	print(output)

	obs_control_before(output)
	time.sleep(60)
	obs_control_after()

def obs_control_before(output):
	if obs_client == None:
		return
	obs_client.set_input_settings(TEXT_ITEM_NAME, {'text': output}, True)
	global zero_gold_alert
	if zero_gold_alert:
		sticker_item_id = obs_client.get_scene_item_id(OBS_SCENE_NAME, STICKER_ITEM_NAME).scene_item_id
		obs_client.set_scene_item_enabled(OBS_SCENE_NAME, sticker_item_id, True)

def obs_control_after():
	if obs_client == None:
		return
	obs_client.set_input_settings(TEXT_ITEM_NAME, {'text': ''}, True)
	sticker_item_id = obs_client.get_scene_item_id(OBS_SCENE_NAME, STICKER_ITEM_NAME).scene_item_id
	obs_client.set_scene_item_enabled(OBS_SCENE_NAME, sticker_item_id, False)

def get_battle_msg(data, isblackout):
	text_list = []
	detail = data["data"]["vsHistoryDetail"]
	teams = [detail['myTeam']] + detail['otherTeams']
	for team in sorted(teams, key=lambda x: x['order']):
		for p in team['players']:
			text_list.append(get_battle_row_text(p, isblackout))
		text_list.append('\n')
	return  ''.join(text_list)

def get_battle_row_text(p,isblackout):
	kill_str = "-"
	death_str = "-"
	ration_str = "-"
	special_str = "-"

	re = p['result']
	if re:
		k = re['kill'] - re['assist']
		kill_str = f"{k}+{re['assist']}"
		death_str = f"{re['death']}"
		special_str = f"{re['special']}"
		ration_str = f"{k / re['death'] if re['death'] else 99:>4.1f}"

	name = p['name']
	if isblackout and not p.get('isMyself'):
		name = "player"
	weapon = (p.get('weapon') or {}).get('name') or ''
	name = f"{name} ({weapon})"

	if p.get('isMyself'):
		name = f"*{name}*"

	return f"{kill_str:>5}k {death_str:>2}d {ration_str:>4} {special_str:>3}sp {p['paint']:>4}p {name}\n"

def get_coop_msg(data, isblackout):
	detail = data["data"]["coopHistoryDetail"]
	msg = f"    {detail['afterGrade']['name']}{detail['afterGradePoint']} 危险度{detail['dangerRate']:.0%}\n"
	
	msg += f"{get_coop_row_text(detail['myResult'], False)}\n"
	for p in detail['memberResults']:
		msg += f"{get_coop_row_text(p, isblackout)}\n"

	flag = 3
	for i, p in enumerate(detail['enemyResults']):
		name = p['enemy']['name']
		if name == '垫肩飞鱼':
			name = '垃圾桶'
		if len(name) == 2:
			name = '  ' + name
		if i % flag == 0:
			msg += "\n "
		msg += f"{name}:{p['teamDefeatCount']:>2}({p['defeatCount']:>2})/{p['popCount']:>2} "

	msg += '\n'

	return msg

def get_coop_row_text(p, isblackout):
	name = p['player']['name']
	if isblackout:
		name = "player"

	global zero_gold_alert
	if p['goldenDeliverCount'] == 0:
		zero_gold_alert = True

	golden = f"{p['goldenDeliverCount']}"
	if p['goldenAssistCount'] > 0:
		golden += f"+{p['goldenAssistCount']}"

	return f"{golden:>5}g {p['deliverCount']:>4}p " \
		f"{p['rescuedCount']:>2}d  {p['rescueCount']:>2}r " \
		f"{p['defeatEnemyCount']:>2}k {name}"
