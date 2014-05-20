function futu_alert(header, text, close, className) {
    /* если div с ID == futu_alerts_holder не найден
		* (окошко вызываетс€ впервые), то создаем необходимые div'ы 
	*/
    if (!document.getElementById('futu_alerts_holder')) {

        var futuAlertOuter = document.createElement('div');
        futuAlertOuter.className = 'futu_alert_outer';
        document.body.appendChild(futuAlertOuter);

        var futuAlertFrame = document.createElement('div');
        futuAlertFrame.className = 'frame';
        futuAlertOuter.appendChild(futuAlertFrame);

        var futuAlertsHolder = document.createElement('div');
        futuAlertsHolder.id = 'futu_alerts_holder';
        futuAlertsHolder.className = 'futu_alerts_holder';
        futuAlertFrame.appendChild(futuAlertsHolder);
    }
    // создаем div с необходимым типом окна
    var futuAlert = document.createElement('div');
    futuAlert.className = 'futu_alert ' + className;
    document.getElementById('futu_alerts_holder').appendChild(futuAlert);
    futuAlert.id = 'futu_alert';

    // создаем div с заголовком окна
    var futuAlertHeader = document.createElement('div');
    futuAlertHeader.className = 'futu_alert_header';
    futuAlert.appendChild(futuAlertHeader);

    futuAlertHeader.innerHTML = header;

    // добавл€ем кнопку закрыти€ окна, если необходимо
    if (close) {
        var futuAlertCloseButton = document.createElement('a');
        futuAlertCloseButton.href = '#';
        futuAlertCloseButton.className = 'futu_alert_close_button';
        futuAlertCloseButton.onclick = function (ev) {
            if (!ev) {
                ev = window.event;
            }
            if (!document.all) ev.preventDefault(); else ev.returnValue = false;
            document.getElementById('futu_alerts_holder').removeChild(futuAlert);
        }
        futuAlert.appendChild(futuAlertCloseButton);

        var futuAlertCloseButtonIcon = document.createElement('img');
        // здесь не забывайте указать свой путь к пиктограмме закрыти€ окна
        futuAlertCloseButtonIcon.src = '/engine/plugins/bookmarks/img/btn_close.gif';
        futuAlertCloseButton.appendChild(futuAlertCloseButtonIcon);
    }

    // создаем div с текстом сообщени€
    var futuAlertText = document.createElement('div');
    futuAlertText.className = 'futu_alert_text';
    futuAlert.appendChild(futuAlertText);


    futuAlertText.innerHTML = text;

    futuAlert.style.position = 'relative';
    futuAlert.style.top = '0';
    futuAlert.style.display = 'block';


    // если сообщение без кнопочки "«акрыть", то вызываем удаление окна через 3 секунды
    if (!close) {
        /* addEvent("click",function(){
		document.getElementById('futu_alerts_holder').removeChild(futuAlert);
		}, document.getElementById('futu_alert')); */
        setTimeout(function () { document.getElementById('futu_alerts_holder').removeChild(futuAlert); }, 3000);

    }
}