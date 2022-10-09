# vpn-client

1. Установить JRE-1.7 или JRE-1.8 на сервере.

2. Скопируйте распакованную директорию vpn-client на диск сервера. Сервер должен иметь доступ к тасикс.
	
	2.1. Откройте файл client-eimzo.conf и заполните поля 
		client.keystore.path=[Путь к файлу ключа полученный от НИЦ НТ ГНК РУз]
		client.keystore.password=[Пароль к файлу ключа полученный от НИЦ НТ ГНК РУз]
		client.keystore.alias=[Алиас ключа полученный от НИЦ НТ ГНК РУз]
	2.2. Добавьте запись 

		127.0.0.5 e-imzo.uz

		в файле 
			c:\Windows\System32\drivers\etc\hosts (для ОС Windows)
			/etc/hosts (для ОС Linux)

3. Запуск.

	3.1. Для запуска vpn-client, наберите команду (в директории  vpn-client)
		для ОС Windows
			run.bat
		или для ОС Linux
			run.sh
	3.2. Для проверки откройте браузер. Если выход в интернет через прокси сервер, то добавьте исплючение для домена e-imzo.uz
		Откройте ссылку http://e-imzo.uz/cams/ocsp
		Сообщение
			HTTP Status 405 - OCSP supports only POST
		означает что vpn работает.
		
 
