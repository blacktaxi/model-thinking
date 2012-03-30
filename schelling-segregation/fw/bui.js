/**
 * Created by PyCharm.
 * User: eis
 * Date: 3/28/12
 * Time: 8:13 PM
 * To change this template use File | Settings | File Templates.
 */
(function() {

window.__ = {
    bind: function bind(viewmodel, attr_name, func) {
        var sig_name = '_sig_'+attr_name+'_changed';
        viewmodel[sig_name].connect(func);
    },

    handle: function handle(viewmodel, event_name, func) {
        viewmodel[event_name].connect(viewmodel, func);
    },

    use_viewmodel: function (viewmodel) {
        viewmodel.bind = function(a, f) { __.bind(viewmodel, a, f); };
        viewmodel.handle = function(a, f) { __.handle(viewmodel, a, f); };
    }
};

})();
