<html>
<head>
	<style>
	</style>
</head>
<body>
% for o in objects:
<table width="100%">
	<tr width="100%">
		<td width="100%">
		% if o.declaration_header:
			${fill_the_parameters(o,o.declaration_header)}
		% endif
		</td>
	</tr>
	<tr>
		<td>
		<div style="width:'80%';float:left;">
		% if o.declaration_content:
			${fill_the_parameters(o,o.declaration_content)}
		% endif
		</div>
		</td>
	</tr>
	<tr>
		<td>
		<div style="width:'80%';float:left;">
		% if o.declaration_footer:
			${fill_the_parameters(o,o.declaration_footer)}
		% endif
		</div>
		</td>
	</tr>
</table>
% endfor
</body>
</html>
