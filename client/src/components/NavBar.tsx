import React, { ReactNode } from 'react'
import {
    Box,
    Flex,
    HStack,
    Link,
    IconButton,
    Button,
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    MenuDivider,
    useDisclosure,
    useColorModeValue,
    Stack,
} from '@chakra-ui/react';
import { ColorModeSwitcher } from "../ColorModeSwitcher";
import {
    Link as RouterLink,
} from "react-router-dom";
import { HamburgerIcon, CloseIcon } from '@chakra-ui/icons';
import Avatar from 'react-avatar';
// import Logo from './Logo';

interface NavLinkProps {
    children: ReactNode;
    to: string;
    onClose?: () => void;
}

interface LinkObject {
    label: string;
    to: string;
}

const Links: LinkObject[] = [
    { label: 'Learn', to: '/' },
    { label: 'Inventory', to: '/inventory'},
    { label: 'Stats', to: '/stats'}
]

const NavLink: React.FC<NavLinkProps> = (props) => (
  <Link
    as={RouterLink}
    px={2}
    py={1}
    rounded={'md'}
    _hover={{
      textDecoration: 'none',
      bg: useColorModeValue('gray.200', 'gray.700'),
    }}
    to={props.to}
    href={'#'}
    onClick={props.onClose}
  >
    {props.children}
  </Link>
);

const NavBar: React.FC = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return (
    <>
      <Box bg={useColorModeValue('gray.100', 'gray.900')} px={4}>
        <Flex h={16} alignItems={'center'} justifyContent={'space-between'}>
          <IconButton
            size={'md'}
            icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
            aria-label={'Open Menu'}
            display={{ md: !isOpen ? 'none' : 'inherit' }}
            onClick={isOpen ? onClose : onOpen}
          />
          <HStack spacing={0} alignItems={'center'}>
            <Box>Logo Placeholder</Box>
            <HStack
              as={'nav'}
              spacing={4}
              display={{ base: 'none', md: 'flex' }}>
              {Links.map((link: LinkObject) => (
                <NavLink key={link.label} to={link.to}>{link.label}</NavLink>
              ))}
            </HStack>
          </HStack>
          <Flex alignItems={'center'}>
            <Menu>

              <MenuButton
                as={Button}
                rounded={'full'}
                variant={'link'}
                cursor={'pointer'}>
                <Avatar size="30" round={true} value="ND" />
              </MenuButton>

              <MenuList>
                <ColorModeSwitcher justifySelf="flex-end" />
                <MenuItem>Link 1</MenuItem>
                <MenuItem>Link 2</MenuItem>
                <MenuDivider />
                <MenuItem>Link 3</MenuItem>
              </MenuList>
            </Menu>
          </Flex>
        </Flex>

        {isOpen ? (
          <Box pb={4}>
            <Stack as={'nav'} spacing={4}>
            {Links.map((link: LinkObject) => (
                <NavLink key={link.label} to={link.to} onClose={onClose}>{link.label}</NavLink>
            ))}
            </Stack>
          </Box>
        ) : null}
      </Box>
    </>
  );
}

export default NavBar;