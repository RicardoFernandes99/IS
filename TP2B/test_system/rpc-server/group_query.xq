declare option output:method "xml";
declare option output:indent "yes";
declare option output:omit-xml-declaration "yes";

declare variable $file external;
declare variable $row external;
declare variable $attr external;
declare variable $filter external;
declare variable $root external;

let $rows :=
  for $r in doc($file)//(*[name() = $row])
  let $val := string(($r/*[name() = $attr])[1])
  where string-length($filter) = 0 or $val = $filter
  group by $g := $val
  return
    <Group>{ attribute { $attr } { $g }, $r }</Group>

return element { $root } { $rows }
