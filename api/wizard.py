#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: wizard.py
"""Run this script to help generate a local_settings.py file."""

# Native python imports
import os

def get_yes_no(prompt_text):
	"""Prompt the user for a yes or no response."""
	confirmation = input(f'{prompt_text} (y/n) ')
	confirmation = confirmation.lower()
	while confirmation not in ['n', 'no', 'y', 'yes']:
		confirmation = input(f'Invalid response. {prompt_text} (y/n) ')

	if confirmation in ['n', 'no']:
		return False
	return True

def main():
	"""Main function that interacts with a user to help configure a local_settings.py file."""
	current_folder = os.path.dirname(os.path.abspath(__file__))
	local_settings_file = os.path.join(current_folder, 'local_settings.py')
	vars_to_set = {
		'NEED_TO_MOUNT': False,
		'NEED_TO_WAKE': False,
		'MOUNT_SHARE_SCRIPT': False,
		'UNMOUNT_SHARE_SCRIPT': False,
		'ALLOWED_ORIGINS': False
	}
	var_vals = {
		'MAGIC_PACKET_MAC_ADDRESS': None,
		'MUSIC_FOLDER': '',
		'ALLOWED_ORIGINS': []
	}

	# If a local config already exists, ask if they want to overwrite it		
	if os.path.exists(local_settings_file):
		confirmation = get_yes_no('You already have a local settings file. Would you like to overwrite it?')
		if confirmation in ['n', 'no']:
			exit()
		else:
			# Check for write access to the file
			if not os.access(local_settings_file, os.W_OK):
				print(f'Sorry, but I can\'t write to {local_settings_file}. Please make sure you are running this script with appropriate privileges.')
				exit(1)
			print()

	else:
		# If the local config file doesn't exist, check for write access to the directory
		if not os.access(current_folder, os.W_OK):
			print(f'Sorry, but I can\'t write to {local_settings_file}. Please make sure you are running this script with appropriate privileges.')
			exit(1)

	print('This script will help you setup your local_settings.py file.')
	print()
	print('What directory is your music stored in? (e.g. /mnt/Music or C:\\\\Music)')
	var_vals['MUSIC_FOLDER'] = input('> ')
	# TODO: sanity check for directory?

	print('In some situations, the device that the music files are hosted on is separate   ')
	print('from the device this API is hosted on. If the device hosting the music files is ')
	print('separate from the device the API is hosted on, the API can run scripts to       ')
	print('unmount and remount the music files if it is unable to read them for any reason.')
	if get_yes_no('Would you like to enable this feature?'):
		vars_to_set['NEED_TO_MOUNT'] = True

		print('Please input the full path of the mounting script.')
		var_vals['MOUNT_SHARE_SCRIPT'] = input('> ')
		# TODO: sanity check for file?

		print('Please input the full path of the unmounting script.')
		var_vals['UNMOUNT_SHARE_SCRIPT'] = input('> ')
		# TODO: sanity check for file?

		print('If the device hosting the music files can fall asleep, the API can also use     ')
		print('magic packets in order to wake it when the files are inaccessible. This requires')
		print('some additional configuration of the device hosting the files. ')
		if get_yes_no('Would you like to enable this feature?'):
			vars_to_set['NEED_TO_WAKE'] = True

			print('Please input the MAC address where the magic packets should be sent.')
			var_vals['MAGIC_PACKET_MAC_ADDRESS'] = input('> ')
			# TODO: sanity check for mac address?


	print('If this API is being hosted with a domain name, you should probably configure   ')
	print('what domain names are allowed to access it. For example, if you have the API    ')
	print('hosted at https://api.example.com, and the web component hosted at              ')
	print('https://example.com, you will need to allow https://example.com as an origin.   ')
	print('By default, this script will only allow http://127.0.0.1.')
	if get_yes_no('Would you like to configure the allowed origins?'):
		all_origins = []
		print('Please input as many origins as you would like to allow.')
		end = False
		while not end:
			curr_origin = input('> ')
			if not curr_origin or len(curr_origin) == 0:
				end = True
			else:
				all_origins.append(curr_origin)

		var_vals['ALLOWED_ORIGINS'] = all_origins
	else:
		var_vals['ALLOWED_ORIGINS'] = [
			'127.0.0.1',
			'http://127.0.0.1'
		]


	# Construct the local_settings.py file from the input components
	local_settings_string = ''
	local_settings_string += '#!/usr/bin/env python\n'
	local_settings_string += '# -*- coding: utf-8 -*-\n'
	local_settings_string += '#Filename: local_settings.py\n'
	local_settings_string += '"""Local settings file."""\n\n'

	local_settings_string += 'MUSIC_FOLDER = \''
	local_settings_string += var_vals['MUSIC_FOLDER'] + '\'\n'

	if vars_to_set['NEED_TO_MOUNT']:
		local_settings_string += 'NEED_TO_MOUNT = True\n'

		local_settings_string += 'MOUNT_SHARE_SCRIPT = \'' 
		local_settings_string += var_vals["MOUNT_SHARE_SCRIPT"] + '\'\n'

		local_settings_string += 'UNMOUNT_SHARE_SCRIPT = \'' 
		local_settings_string += var_vals['UNMOUNT_SHARE_SCRIPT'] + '\'\n'

		if vars_to_set['NEED_TO_WAKE']:
			local_settings_string += 'NEED_TO_WAKE = True\n'

			local_settings_string += 'MAGIC_PACKET_MAC_ADDRESS = \''
			local_settings_string += var_vals['MAGIC_PACKET_MAC_ADDRESS'] + '\'\n'

	local_settings_string += '\n'
	local_settings_string += 'ALLOWED_ORIGINS = [\n'
	for origin in var_vals['ALLOWED_ORIGINS']:
		local_settings_string += '    \'' + origin + '\',\n'
	local_settings_string += ']\n'

	with open(local_settings_file, 'w') as f:
		f.write(local_settings_string)

	print()
	print('Your local_settings.py file has been successfully created. Before the server    ')
	print('will run correctly, you will need to initialize the database. You can do this by')
	print('running "python main.py". This will create the database, and attempt to load the')
	print('music library.')
	print()

if __name__ == "__main__":
	main()