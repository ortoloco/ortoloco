/*global define, google */
define(['modules/depotDistance'], function (depotDistance) {

    $(function () {
        if (window.google) {
            var initialize = function () {
                var mapOptions = {
                    zoom: 14,
                    center: new google.maps.LatLng(47.424566, 8.517524),
                    mapTypeId: google.maps.MapTypeId.ROADMAP
                };

                var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

                depotDistance.createDepotOnMap(map, '<font color="#709f4a"><strong>meh als gmües</strong></font>-Feld', 'Reckenholzstr. 150', '8046', 'Zürich', 47.424566, 8.517524);
            };

            google.maps.event.addDomListener(window, 'load', initialize);
        }
    });
});