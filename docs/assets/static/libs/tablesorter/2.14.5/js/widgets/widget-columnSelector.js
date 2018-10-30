/* Column Selector/Responsive table widget (beta) for TableSorter 12/17/2013 (v2.14.6)
 * Requires tablesorter v2.8+ and jQuery 1.7+
 * by Justin Hallett & Rob Garrison
 */
/*jshint browser:true, jquery:true, unused:false */
/*global jQuery: false */
;(function($){
"use strict";

var ts = $.tablesorter,
namespace = '.tscolsel',
tsColSel = ts.columnSelector = {

	queryAll   : '@media only all { [columns] { display: none; } }',
	queryBreak : '@media screen and (min-width: [size]) { [columns] { display: table-cell; } }',

	init: function(table, c, wo) {
		var colSel;

		// unique table class name
		c.tableId = 'tablesorter' + new Date().getTime();
		c.$table.addClass( c.tableId );

		// build column selector/state array
		colSel = c.selector = { $container : $(wo.columnSelector_container) };
		tsColSel.setupSelector(table, c, wo);

		if (wo.columnSelector_mediaquery) {
			tsColSel.setupBreakpoints(c, wo);
		}

		if (colSel.$container.length) {
			colSel.$style = $('<style></style>').prop('disabled', true).appendTo('head');
			tsColSel.updateCols(c, wo);
		}

	},

	setupSelector: function(table, c, wo) {
		var name,
			colSel = c.selector,
			$container = colSel.$container,
			// get stored column states
			saved = wo.columnSelector_saveColumns && ts.storage ? ts.storage( table, 'tablesorter-columnSelector' ) : [];

		// initial states
		colSel.states = [];
		colSel.$column = [];
		colSel.$wrapper = [];
		colSel.$checkbox = [];
		// populate the selector container
		c.$table.children('thead').find('tr:first th', table).each(function() {
			var $this = $(this),
				// if no data-priority is assigned, default to 1, but don't remove it from the selector list
				priority = $this.attr(wo.columnSelector_priority) || 1,
				colId = $this.attr('data-column');

			// if this column not hidable at all
			// include getData check (includes "columnSelector-false" class, data attribute, etc)
			if ( isNaN(priority) && priority.length > 0 || ts.getData(this, c.headers[colId], 'columnSelector') == 'false' ||
				( wo.columnSelector_columns[colId] && wo.columnSelector_columns[colId] === 'disable') ) {
				return true; // goto next
			}

			// set default state
			colSel.states[colId] = saved && typeof(saved[colId]) !== 'undefined' ?
				saved[colId] : typeof(wo.columnSelector_columns[colId]) !== 'undefined' ? wo.columnSelector_columns[colId] : true;
			colSel.$column[colId] = $(this);

			// set default col title
			name = $this.attr(wo.columnSelector_name) || $this.text();

			if ($container.length) {
				colSel.$wrapper[colId] = $(wo.columnSelector_layout.replace(/\{name\}/g, name)).appendTo($container);
				colSel.$checkbox[colId] = colSel.$wrapper[colId]
					.find('input')
					.attr('data-column', colId)
					.prop('checked', colSel.states[colId])
					.bind('change', function(){
						colSel.states[colId] = this.checked;
						tsColSel.updateCols(c, wo);
					}).change();
			}
		});

	},

	setupBreakpoints: function(c, wo){
		var colSel = c.selector;

		// add responsive breakpoints
		if (wo.columnSelector_mediaquery) {
			// used by window resize function
			colSel.lastIndex = -1;
			wo.columnSelector_breakpoints.sort();
			colSel.$breakpoints = $('<style></style>').prop('disabled', true).appendTo('head');
			tsColSel.updateBreakpoints(c, wo);
			c.$table.unbind('updateAll' + namespace).bind('updateAll' + namespace, function(){
				tsColSel.updateBreakpoints(c, wo);
				tsColSel.updateCols(c, wo);
			});
		}

		if (colSel.$container.length) {
			// Add media queries toggle
			if (wo.columnSelector_mediaquery && wo.columnSelector_mediaquery) {
				$( wo.columnSelector_layout.replace(/\{name\}/g, wo.columnSelector_mediaqueryName) )
					.prependTo(colSel.$container)
					.find('input')
					.prop('checked', wo.columnSelector_mediaqueryState)
					.bind('change', function(){
						wo.columnSelector_mediaqueryState = this.checked;
						$.each( colSel.$checkbox, function(i, $cb){
							if ($cb) {
								$cb[0].disabled = wo.columnSelector_mediaqueryState;
								colSel.$wrapper[i].toggleClass('disabled', wo.columnSelector_mediaqueryState);
							}
						});
						tsColSel.updateBreakpoints(c, wo);
						tsColSel.updateCols(c, wo);
					}).change();
			}
			// Add a bind on update to re-run col setup
			c.$table.unbind('update' + namespace).bind('update' + namespace, function() {
				tsColSel.updateCols(c, wo);
			});
		}
	},


	updateBreakpoints: function(c, wo){
		var priority, column, breaks,
			colSel = c.selector,
			prefix = '.' + c.tableId,
			mediaAll = [],
			breakpts = '';
		if (wo.columnSelector_mediaquery && !wo.columnSelector_mediaqueryState) {
			colSel.$breakpoints.prop('disabled', true);
			colSel.$style.prop('disabled', false);
			return;
		}

		// only 6 breakpoints (same as jQuery Mobile)
		for (priority = 0; priority < 6; priority++){
			/*jshint loopfunc:true */
			breaks = [];
			c.$headers.filter('[' + wo.columnSelector_priority + '=' + (priority + 1) + ']').each(function(){
				column = parseInt($(this).attr('data-column'), 10) + 1;
				breaks.push(prefix + ' tr th:nth-child(' + column + ')');
				breaks.push(prefix + ' tr td:nth-child(' + column + ')');
			});
			if (breaks.length) {
				mediaAll = mediaAll.concat( breaks );
				breakpts += tsColSel.queryBreak
					.replace(/\[size\]/g, wo.columnSelector_breakpoints[priority])
					.replace(/\[columns\]/g, breaks.join(','));
			}
		}
		if (colSel.$style) { colSel.$style.prop('disabled', true); }
		colSel.$breakpoints.prop('disabled', false)
			.html( tsColSel.queryAll.replace(/\[columns\]/g, mediaAll.join(',')) + breakpts );

	},

	updateCols: function(c, wo) {
		if (wo.columnSelector_mediaquery && wo.columnSelector_mediaqueryState) {
			return;
		}
		var column,
			styles = [],
			prefix = '.' + c.tableId;
		c.selector.$container.find('input[data-column]').each(function(){
			if (!this.checked) {
				column = parseInt( $(this).attr('data-column'), 10 ) + 1;
				styles.push(prefix + ' tr th:nth-child(' + column + ')');
				styles.push(prefix + ' tr td:nth-child(' + column + ')');
			}
		});
		if (wo.columnSelector_mediaquery){
			c.selector.$breakpoints.prop('disabled', true);
		}
		if (c.selector.$style) {
			c.selector.$style.prop('disabled', false).html( styles.join(',') + ' { display: none; }' );
		}
		if (wo.columnSelector_saveColumns && ts.storage) {
			ts.storage( c.$table[0], 'tablesorter-columnSelector', c.selector.states );
		}
	}

};

ts.addWidget({
	id: "columnSelector",
	priority: 10,
	options: {
		// target the column selector markup
		columnSelector_container : null,
		// column status, true = display, false = hide
		// disable = do not display on list
		columnSelector_columns : {},
		// remember selected columns
		columnSelector_saveColumns: true,

		// container layout
		columnSelector_layout : '<label><input type="checkbox">{name}</label>',
		// data attribute containing column name to use in the selector container
		columnSelector_name  : 'data-selector-name',

		/* Responsive Media Query settings */
		// enable/disable mediaquery breakpoints
		columnSelector_mediaquery: true,
		// toggle checkbox name
		columnSelector_mediaqueryName: 'Auto: ',
		// breakpoints checkbox initial setting
		columnSelector_mediaqueryState: true,
		// responsive table hides columns with priority 1-6 at these breakpoints
		// see http://view.jquerymobile.com/1.3.2/dist/demos/widgets/table-column-toggle/#Applyingapresetbreakpoint
		// *** set to false to disable ***
		columnSelector_breakpoints : [ '20em', '30em', '40em', '50em', '60em', '70em' ],
		// data attribute containing column priority
		// duplicates how jQuery mobile uses priorities:
		// http://view.jquerymobile.com/1.3.2/dist/demos/widgets/table-column-toggle/
		columnSelector_priority : 'data-priority'

	},
	init: function(table, thisWidget, c, wo) {
		tsColSel.init(table, c, wo);
	},
	remove: function(table, c){
		var csel = c.selector;
		csel.$container.empty();
		csel.$style.remove();
		csel.$breakpoints.remove();
		c.$table.unbind('updateAll' + namespace + ',update' + namespace);
	}

});

})(jQuery);
